import concurrent.futures
import json
import logging
import os
import shutil
import subprocess
import time
import traceback
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional, Tuple, Callable, Any

import instructor
import litellm
import pandas as pd
from tqdm.auto import tqdm

from moatless.benchmark.report_v2 import to_result, BenchmarkResult, to_dataframe
from moatless.edit import PlanToCode
from moatless.state import Pending, Finished, Rejected
from moatless.trajectory import Trajectory
from moatless.transition_rules import TransitionRules, TransitionRule
from moatless.benchmark.swebench import (
    load_instance,
    create_workspace,
)
from moatless.benchmark.utils import (
    trace_metadata,
)
from moatless.loop import AgenticLoop
from moatless.repository import GitRepository


logger = logging.getLogger(__name__)


class Evaluation:
    def __init__(
        self,
        evaluations_dir: str,
        evaluation_name: str,
        transitions: TransitionRules,
        dataset_name: str = "princeton-nlp/SWE-bench_Lite",
        report_mode: str | None = None,
        max_cost: float = 0.5,
        max_transitions: int = 25,
        use_perfect_file_context: bool = False,
        reward_threshold: Optional[float] = None,
        num_iterations: int = 25,
        max_expansions: int = 2,
        max_file_context_tokens: int = 16000,
        litellm_callback: Optional[str] = None,
        previous_trajectory_dir: Optional[str] = None,
        retry_state: Optional[str] = None,
        retry_trajectory: bool = False,
        num_workers: int = 1,
        use_testbed: bool = False,
        eval_func: Callable[[dict, Trajectory], bool] = None,
        **kwargs,
    ):
        self.evaluations_dir = evaluations_dir
        self.num_workers = num_workers
        self.report_mode = report_mode
        self.dataset_name = dataset_name
        self.evaluation_name = evaluation_name
        self.retry_trajectory = retry_trajectory

        self.eval_func = eval_func

        self.use_testbed = use_testbed

        self.use_perfect_file_context = use_perfect_file_context

        self.max_file_context_tokens = max_file_context_tokens
        self.max_cost = max_cost
        self.max_expansions = max_expansions
        self.max_transitions = max_transitions
        self.num_iterations = num_iterations
        self.reward_threshold = reward_threshold
        self.transitions = transitions

        litellm.drop_params = True

        self.evaluation_dir = f"{evaluations_dir}/{evaluation_name}"
        self.repo_base_dir = os.getenv("REPO_DIR", "/tmp/repos")
        self.predictions_path = f"{self.evaluation_dir}/all_preds.jsonl"
        logger.info(f"Evaluation directory: {self.evaluation_dir}")

        self.previous_trajectory_dir = previous_trajectory_dir
        logger.info(f"Previous trajectory directory: {self.previous_trajectory_dir}")
        self.retry_state = retry_state

        if litellm_callback:
            litellm.success_callback = [litellm_callback]
            litellm.failure_callback = [litellm_callback]

        # This is only to set instances as resolved after all evaluations have been run to generate the report
        # TODO: Run swe-bench-docker after the prediction is generated
        result_file = f"{self.evaluation_dir}/result.json"
        if os.path.exists(result_file):
            with open(os.path.join(result_file)) as f:
                self.report = json.load(f)
        else:
            self.report = {"resolved_ids": []}

    def run_evaluation(
        self,
        split: str = "lite",
        resolved_by: Optional[int] = None,
        instance_ids: list[str] | None = None,
        ignore_repos: list[str] | None = None,
    ):
        file_path = os.path.join(
            os.path.dirname(__file__), f"swebench_{split}_all_evaluations.json"
        )
        with open(file_path) as f:
            instances = json.load(f)

        instances = sorted(instances, key=lambda x: len(x["resolved_by"]), reverse=True)
        logger.info(f"Loaded {len(instances)} instances from {file_path}")

        instances = [
            instance for instance in instances if "sympy" not in instance["instance_id"]
        ]

        if instance_ids:
            instances = [
                instance
                for instance in instances
                if instance["instance_id"] in instance_ids
            ]

            logger.info(
                f"Running evaluation for {len(instances)} instances filtered by instance_ids"
            )

        if resolved_by:
            instances = [
                instance
                for instance in instances
                if len(instance["resolved_by"]) >= resolved_by
            ]

            logger.info(
                f"Running evaluation for {len(instances)} instances filtered by resolved_by >= {resolved_by}"
            )

        if ignore_repos:
            instances = [
                instance
                for instance in instances
                if instance["repo"] not in ignore_repos
            ]

        if instances:
            logger.info(
                f"Running evaluation for {len(instances)} instances after filtering by ignore_repos"
            )

        return self._run_evaluation(instances)

    def run_single_instance(
        self,
        instance_id: str,
        dataset: str = "princeton-nlp/SWE-bench_Lite",
        split="test",
    ) -> BenchmarkResult:
        instance = load_instance(instance_id, dataset, split)
        trajectory = self._evaluate_instance(instance)
        return to_result(instance, trajectory, self.report)

    def _evaluate_instance(self, instance: dict) -> Trajectory:
        instance_id = instance["instance_id"]

        trajectory_path = os.path.join(
            self.evaluation_dir, f"{instance_id}/trajectory.json"
        )
        if not os.path.exists(self.evaluation_dir):
            os.makedirs(trajectory_path)

        if os.path.exists(trajectory_path) and not self.retry_trajectory:
            # TODO: Retry when failed or not finished?
            trajectory = Trajectory.load(trajectory_path, skip_workspace=True)
            status = trajectory.info.get("status")
            if status and status != "error":
                logger.info(
                    f"Skipping {instance_id} because it has already been evaluated with status {trajectory.info.get('status')}"
                )
                return trajectory

        problem_statement = instance["problem_statement"]

        testbed = None
        if self.use_testbed:
            from testbed.client.manager import TestbedManager

            manager = TestbedManager(
                namespace="testbed-dev", dataset_name=self.dataset_name
            )
            testbed = manager.get_or_create_testbed(
                instance_id,
                timeout=1200,
                log_dir=f"{self.evaluation_dir}/{instance_id}",
            )

        workspace = create_workspace(
            instance,
            repo_base_dir=self.repo_base_dir,
            create_instance_dir=True,
            testbed=testbed,
            use_perfect_file_context=self.use_perfect_file_context,
            max_file_context_tokens=self.max_file_context_tokens,
        )

        previous_actions = None
        if self.previous_trajectory_dir:
            previous_trajectory_path = os.path.join(
                self.previous_trajectory_dir, f"{instance_id}/trajectory.json"
            )
            if os.path.exists(previous_trajectory_path):
                previous_trajectory = Trajectory.load(previous_trajectory_path)
                previous_actions = previous_trajectory.get_mocked_actions()
            else:
                # Version 1
                previous_trajectory_path = os.path.join(
                    self.previous_trajectory_dir, f"{instance_id}.json"
                )
                previous_trajectory = self.read_trajectory(previous_trajectory_path)
                if previous_trajectory:
                    previous_actions = self.get_actions(previous_trajectory)

        metadata = trace_metadata(
            instance_id=instance_id,
            session_id=self.evaluation_name,
            trace_name="moatless",
        )

        loop = AgenticLoop(
            transition_rules=self.transitions,
            initial_message=problem_statement,
            workspace=workspace,
            metadata=metadata,
            reset_mocks_at_state=self.retry_state,
            mocked_actions=previous_actions,
            continue_after_mocks=True,
            trajectory_path=trajectory_path,
            max_cost=self.max_cost,
            max_transitions=self.max_transitions,
            num_iterations=self.num_iterations,
            max_actions=self.max_expansions,
        )

        info: dict[str, Any] = {
            "evaluation_name": self.evaluation_name,
            "instance_id": instance["instance_id"],
        }

        loop.trajectory.save_info(info)

        start_time = time.time()
        try:
            response = loop.run()

            info["status"] = response.status
        except Exception:
            info["error"] = traceback.format_exc()
            info["status"] = "error"
            logging.exception(f"Error in evaluation of {instance['instance_id']} ")
        finally:
            info["duration"] = time.time() - start_time
            usage = loop.total_usage()
            info["total_cost"] = usage.completion_cost
            info["prompt_tokens"] = usage.prompt_tokens
            info["completion_tokens"] = usage.completion_tokens

            if self.eval_func:
                try:
                    info["eval_func"] = self.eval_func(instance, loop.trajectory)
                except Exception:
                    logging.exception(
                        f"Error in evaluation of {instance['instance_id']} "
                    )

            if isinstance(workspace.file_repo, GitRepository):
                test_patch_files = instance.get("test_file_spans", {}).keys()
                diff = workspace.file_repo.diff(ignore_paths=test_patch_files)
            else:
                output = subprocess.run(
                    ["git", "diff"],
                    capture_output=True,
                    text=True,
                    cwd=workspace.file_repo.repo_dir,
                )

                if output:
                    diff = output.stdout
                else:
                    diff = None

            if diff and not diff.endswith("\n"):
                diff += "\n"

            info["submission"] = diff

            if diff and testbed:
                result = testbed.run_evaluation(run_id=instance_id, patch=diff)
                info["resolved"] = result.resolved
                info["evaluation_result"] = result.model_dump()

            if testbed:
                testbed.close()

            loop.trajectory.save_info(info)
            if testbed:
                testbed.close()

            shutil.rmtree(workspace.file_repo.repo_dir)

        return loop.trajectory

    def _to_csv_report(self, results: list[BenchmarkResult]):
        df = to_dataframe(results, self.report_mode)
        df.to_csv(
            f"{self.evaluation_dir}/result.csv",
            index=False,
            sep=",",
            decimal=",",
            quoting=1,
        )

    def _run_evaluation(self, instances: list[dict]):
        if not os.path.exists(self.evaluation_dir):
            os.makedirs(self.evaluation_dir)

        if self.num_workers > 1:
            self._run_evaluation_threads(instances)
        else:
            self._run_evaluation_simple(instances)

        if self.repo_base_dir in self.evaluations_dir:
            shutil.rmtree(self.repo_base_dir)

    def process_instance(self, instance):
        try:
            trajectory = self._evaluate_instance(instance)
            if not trajectory:
                return None

            result = to_result(instance, trajectory, self.report)

            prediction = {
                "model_name_or_path": self.evaluation_name,
                "instance_id": instance["instance_id"],
                "model_patch": trajectory.info.get("submission", ""),
            }

            with open(self.predictions_path, "a") as file:
                json_string = json.dumps(prediction)
                file.write(json_string + "\n")

            return result
        except Exception:
            logger.exception(f"Error in processing instance {instance['instance_id']}")
            return None

    def _run_evaluation_threads(self, instances: list[dict]):
        error = 0

        with open(self.predictions_path, "w") as file:
            file.write("")

        results = []

        logger.info(
            f"Processing {len(instances)} instances with {self.num_workers} workers"
        )
        logger.info(self.transitions)

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=self.num_workers
        ) as executor:
            futures = [
                executor.submit(self.process_instance, instance)
                for instance in instances
            ]

            pbar = tqdm(concurrent.futures.as_completed(futures), total=len(futures))

            for future in pbar:
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        self._to_csv_report(results)
                        self._save_json_report(results)
                    else:
                        error += 1

                    stats = self._create_stats(results)
                    pbar.set_postfix(stats)
                except Exception:
                    error += 1
                    logger.exception("Error in processing instance")

        logger.info(f"Completed processing with {error} errors")

    def _create_stats(self, results):
        stats = {}
        if results:
            stats["avg_duration"] = sum(r.duration for r in results) / len(results)
            stats["avg_cost"] = sum(r.total_cost for r in results) / len(results)
            stats["total_cost"] = sum(r.total_cost for r in results)

            identified = sum(
                1
                for r in results
                if r.status in ["identified", "planned", "edited", "resolved"]
            )
            resolved = sum(1 for r in results if r.status in ["resolved"])
            error = sum(1 for r in results if r.status == "error")

            if identified > 0:
                stats["identified"] = f"{(identified / len(results)) * 100:.2f}%"
            if resolved > 0:
                stats["resolved"] = f"{(resolved / len(results)) * 100:.2f}%"
            stats["error"] = error

        return stats

    def _run_evaluation_simple(self, instances: list[dict]):
        with open(self.predictions_path, "w") as file:
            file.write("")

        results = []
        pbar = tqdm(instances)
        for instance in pbar:
            trajectory = self._evaluate_instance(instance)
            if not trajectory:
                continue

            try:
                result = to_result(instance, trajectory, report=self.report)
                results.append(result)
                self._to_csv_report(results)
                self._save_json_report(results)
            except Exception:
                logging.exception(
                    f"Error when generating report for instance {instance['instance_id']}"
                )

            stats = self._create_stats(results)
            pbar.set_postfix(stats)

            prediction = {
                "model_name_or_path": self.evaluation_name,
                "instance_id": instance["instance_id"],
                "model_patch": trajectory.info.get("submission", ""),
            }

            with open(self.predictions_path, "a") as file:
                json_string = json.dumps(prediction)
                file.write(json_string + "\n")

    def _save_json_report(self, results: list[BenchmarkResult]):
        json_results = [result.model_dump() for result in results]
        with open(f"{self.evaluation_dir}/report.json", "w") as f:
            json.dump(json_results, f, indent=2)

    def read_trajectory(self, path) -> dict | None:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        else:
            return None

    def get_actions(self, trajectory: dict):
        actions = []
        for transition in trajectory["transitions"]:
            for action in transition["actions"]:
                actions.append(action["action"])
        return actions


def create_evaluation_name(
    name: str,
    model: str,
):
    date_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
    model_name = model.split("/")[-1]
    return f"{date_str}_{name}_{model_name}"
