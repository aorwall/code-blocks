from moatless.schema import FileWithSpans

from moatless.benchmark.swebench import (
    setup_swebench_repo,
    create_workspace,
    create_index,
)
from moatless.benchmark.utils import get_moatless_instance, get_moatless_instances
from moatless.index import IndexSettings, CodeIndex
from moatless.index.settings import CommentStrategy
from moatless.repository import GitRepository, FileRepository

import pytest
from moatless.index.code_index import is_test


@pytest.mark.parametrize(
    "file_path, expected",
    [
        # Test files in test directories
        ("tests/test_file.py", True),
        ("test/file_test.py", True),
        ("src/tests/unit/test_module.py", True),
        # Test files with test_ prefix
        ("test_requests.py", True),
        ("api/test_views.py", True),
        # Test files with _test suffix
        ("utils_test.py", True),
        ("models/user_test.py", True),
        # Non-test files
        ("main.py", False),
        ("utils.py", False),
        ("api/views.py", False),
        # Edge cases
        ("testing_utils.py", False),  # Contains "test" but not a test file
        ("contest_results.py", False),  # Contains "test" but not a test file
        ("test_data/sample.py", False),
        ("tests/data/sample_data.py", False),
        # Subdirectories with "test" in the name
        ("test_suite/helpers.py", False),
        ("integration_tests/conftest.py", False),
        # Files with "test" in the middle of the name
        ("my_test_utils.py", False),
        ("tests/my_test_utils.py", False),
        # Additional cases
        ("tests/functional/test_api.py", True),
        ("src/package/tests/integration/test_database.py", True),
        ("docs/test_documentation.md", False),  # Not a .py file
        ("test.py", True),  # Simple test file in root
        ("subpackage/test/__init__.py", False),  # __init__.py in test directory
    ],
)
def test_is_test(file_path, expected):
    assert is_test(file_path) == expected


def test_all_instance_test_fils():
    instances = get_moatless_instances()
    missed_test_files = []

    for instance_id, instance in instances.items():
        for test_file in instance["test_file_spans"].keys():
            if not is_test(test_file):
                missed_test_files.append(f"{instance_id}\t{test_file}")

        for expected_file in instance["expected_spans"].keys():
            assert not is_test(
                expected_file
            ), f"{expected_file} for {instance_id} is a test file"

    for missed_test_file in missed_test_files:
        print(missed_test_file)

    assert (
        len(missed_test_files) < 25
    ), f"Expected less than 25 missed test files. Got {len(missed_test_files)} missed matches."


def test_find_test_files():
    instance_id = "sympy__sympy-11400"
    instance = get_moatless_instance(instance_id)
    workspace = create_workspace(instance)

    files = workspace.code_index.find_test_files(
        "sympy/printing/ccode.py", max_results=3
    )
    assert len(files) == 3
    assert files == [
        FileWithSpans(
            file_path="sympy/printing/tests/test_ccode.py",
            span_ids=[
                "test_ccode_sqrt",
                "test_printmethod",
                "test_ccode_Assignment",
                "test_ccode_For",
                "test_ccode_reserved_words",
                "test_ccode_sign",
                "test_ccode_Integer",
                "test_ccode_Rational",
                "test_ccode_constants_mathh",
                "test_ccode_constants_other",
                "test_ccode_exceptions",
                "test_ccode_functions",
                "test_ccode_inline_function",
                "test_ccode_user_functions",
                "test_ccode_ITE",
                "test_ccode_Indexed",
                "test_ccode_Indexed_without_looking_for_contraction",
                "test_ccode_settings",
                "test_ccode_Piecewise_deep",
                "test_ccode_Pow",
            ],
        ),
        FileWithSpans(
            file_path="sympy/utilities/tests/test_codegen.py",
            span_ids=[
                "test_c_code_reserved_words",
                "test_empty_c_code",
                "test_empty_c_code_with_comment",
                "test_empty_c_header",
                "test_numbersymbol_c_code",
                "test_simple_c_code",
            ],
        ),
        FileWithSpans(
            file_path="sympy/printing/tests/test_fcode.py",
            span_ids=[
                "test_fcode_Float",
                "test_fcode_Integer",
                "test_fcode_Rational",
                "test_fcode_functions",
                "test_fcode_functions_with_integers",
            ],
        ),
    ]


def test_find_test_files_with_filename_match_but_low_semantic_rank():
    instance_id = "sympy__sympy-12236"
    instance = get_moatless_instance(instance_id)
    workspace = create_workspace(instance)

    files = workspace.code_index.find_test_files(
        "sympy/polys/domains/polynomialring.py", max_results=3, max_spans=1
    )
    assert len(files) == 3
    assert files == [
        FileWithSpans(
            file_path="sympy/polys/domains/tests/test_polynomialring.py",
            span_ids=["test_units"],
        ),
        FileWithSpans(
            file_path="sympy/polys/tests/test_rings.py", span_ids=["test_sring"]
        ),
        FileWithSpans(
            file_path="sympy/polys/domains/tests/test_domains.py",
            span_ids=["test_PolynomialRing_from_FractionField"],
        ),
    ]


def test_find_test_files_by_span():
    instance_id = "django__django-13315"
    instance = get_moatless_instance(instance_id)
    workspace = create_workspace(instance)

    files = workspace.code_index.find_test_files(
        "django/db/models/fields/related.py",
        span_id="ForeignKey.formfield",
        max_results=3,
    )
    assert len(files) == 3
    assert files == [
        FileWithSpans(
            file_path="tests/model_meta/tests.py",
            span_ids=[
                "PrivateFieldsTests.test_private_fields",
                "RelatedObjectsTests.key_name",
                "RelatedObjectsTests.test_related_objects",
                "RelatedObjectsTests.test_related_objects_include_hidden",
                "RelatedObjectsTests.test_related_objects_include_hidden_local_only",
                "RelatedObjectsTests.test_related_objects_local",
            ],
        ),
        FileWithSpans(
            file_path="tests/model_forms/tests.py",
            span_ids=["OtherModelFormTests.test_foreignkeys_which_use_to_field"],
        ),
        FileWithSpans(
            file_path="tests/forms_tests/tests/tests.py",
            span_ids=[
                "ModelFormCallableModelDefault.test_callable_initial_value",
                "ModelFormCallableModelDefault.test_no_empty_option",
            ],
        ),
    ]


def test_find_test_function():
    instance_id = "django__django-13768"
    instance = get_moatless_instance(instance_id)
    workspace = create_workspace(instance)

    files = workspace.code_index.find_test_files(
        "django/dispatch/dispatcher.py", max_results=3, max_spans=1
    )
    for file in files:
        assert "test" in file.span_ids[0].lower()


def test_find_test_function():
    instance_id = "django__django-12983"
    instance = get_moatless_instance(instance_id)
    workspace = create_workspace(instance)

    query = """set_ticks"""
    files = workspace.code_index.find_test_files(
        "django/utils/text.py", query=query, max_results=3, max_spans=1
    )
    for file in files:
        print(file)
        assert "test" in file.span_ids[0].lower()


def test_ingestion():
    index_settings = IndexSettings(
        embed_model="voyage-code-2",
        dimensions=1536,
        language="python",
        min_chunk_size=200,
        chunk_size=750,
        hard_token_limit=3000,
        max_chunks=200,
        comment_strategy=CommentStrategy.ASSOCIATE,
    )

    instance_id = "django__django-12419"
    instance = get_moatless_instance(instance_id, split="verified")
    repo_dir = setup_swebench_repo(instance)
    print(repo_dir)
    repo = FileRepository(repo_dir)
    code_index = CodeIndex(settings=index_settings, file_repo=repo)

    vectors, indexed_tokens = code_index.run_ingestion(
        num_workers=1, input_files=["django/conf/global_settings.py"]
    )

    results = code_index._vector_search("SECURE_REFERRER_POLICY setting")

    for result in results:
        print(result)


def test_wildcard_file_patterh():
    instance_id = "django__django-12039"
    file_pattern = "**/*.py"
    query = "Index class implementation and CREATE INDEX SQL generation"

    instance = get_moatless_instance(instance_id, split="verified")
    code_index = create_index(instance)

    results = code_index.search(
        query, file_pattern=file_pattern, max_results=250, max_tokens=8000
    )

    for result in results.hits:
        print(result)
