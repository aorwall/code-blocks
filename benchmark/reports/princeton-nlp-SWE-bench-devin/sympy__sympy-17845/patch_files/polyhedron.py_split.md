

## EpicSplitter

17 chunks

#### Split 1
242 tokens, line: 1 - 394

```python
from __future__ import print_function, division

from sympy.combinatorics import Permutation as Perm
from sympy.combinatorics.perm_groups import PermutationGroup
from sympy.core import Basic, Tuple
from sympy.core.compatibility import as_int, range
from sympy.sets import FiniteSet
from sympy.utilities.iterables import (minlex, unflatten, flatten)

rmul = Perm.rmul


class Polyhedron(Basic):
    """
    Represents the polyhedral symmetry group (PSG).

    The PSG is one of the symmetry groups of the Platonic solids.
    There are three polyhedral groups: the tetrahedral group
    of order 12, the octahedral group of order 24, and the
    icosahedral group of order 60.

    All doctests have been given in the docstring of the
    constructor of the object.

    References
    ==========

    http://mathworld.wolfram.com/PolyhedralGroup.html
    """
    _edges = None

    def __new__(cls, corners, faces=[], pgroup=[]):
        # ... other code
```



#### Split 2
3696 tokens, line: 33 - 382

```python
class Polyhedron(Basic):

    def __new__(cls, corners, faces=[], pgroup=[]):
        """
        The constructor of the Polyhedron group object.

        It takes up to three parameters: the corners, faces, and
        allowed transformations.

        The corners/vertices are entered as a list of arbitrary
        expressions that are used to identify each vertex.

        The faces are entered as a list of tuples of indices; a tuple
        of indices identifies the vertices which define the face. They
        should be entered in a cw or ccw order; they will be standardized
        by reversal and rotation to be give the lowest lexical ordering.
        If no faces are given then no edges will be computed.

            >>> from sympy.combinatorics.polyhedron import Polyhedron
            >>> Polyhedron(list('abc'), [(1, 2, 0)]).faces
            {(0, 1, 2)}
            >>> Polyhedron(list('abc'), [(1, 0, 2)]).faces
            {(0, 1, 2)}

        The allowed transformations are entered as allowable permutations
        of the vertices for the polyhedron. Instance of Permutations
        (as with faces) should refer to the supplied vertices by index.
        These permutation are stored as a PermutationGroup.

        Examples
        ========

        >>> from sympy.combinatorics.permutations import Permutation
        >>> Permutation.print_cyclic = False
        >>> from sympy.abc import w, x, y, z

        Here we construct the Polyhedron object for a tetrahedron.

        >>> corners = [w, x, y, z]
        >>> faces = [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 2, 3)]

        Next, allowed transformations of the polyhedron must be given. This
        is given as permutations of vertices.

        Although the vertices of a tetrahedron can be numbered in 24 (4!)
        different ways, there are only 12 different orientations for a
        physical tetrahedron. The following permutations, applied once or
        twice, will generate all 12 of the orientations. (The identity
        permutation, Permutation(range(4)), is not included since it does
        not change the orientation of the vertices.)

        >>> pgroup = [Permutation([[0, 1, 2], [3]]), \
                      Permutation([[0, 1, 3], [2]]), \
                      Permutation([[0, 2, 3], [1]]), \
                      Permutation([[1, 2, 3], [0]]), \
                      Permutation([[0, 1], [2, 3]]), \
                      Permutation([[0, 2], [1, 3]]), \
                      Permutation([[0, 3], [1, 2]])]

        The Polyhedron is now constructed and demonstrated:

        >>> tetra = Polyhedron(corners, faces, pgroup)
        >>> tetra.size
        4
        >>> tetra.edges
        {(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)}
        >>> tetra.corners
        (w, x, y, z)

        It can be rotated with an arbitrary permutation of vertices, e.g.
        the following permutation is not in the pgroup:

        >>> tetra.rotate(Permutation([0, 1, 3, 2]))
        >>> tetra.corners
        (w, x, z, y)

        An allowed permutation of the vertices can be constructed by
        repeatedly applying permutations from the pgroup to the vertices.
        Here is a demonstration that applying p and p**2 for every p in
        pgroup generates all the orientations of a tetrahedron and no others:

        >>> all = ( (w, x, y, z), \
                    (x, y, w, z), \
                    (y, w, x, z), \
                    (w, z, x, y), \
                    (z, w, y, x), \
                    (w, y, z, x), \
                    (y, z, w, x), \
                    (x, z, y, w), \
                    (z, y, x, w), \
                    (y, x, z, w), \
                    (x, w, z, y), \
                    (z, x, w, y) )

        >>> got = []
        >>> for p in (pgroup + [p**2 for p in pgroup]):
        ...     h = Polyhedron(corners)
        ...     h.rotate(p)
        ...     got.append(h.corners)
        ...
        >>> set(got) == set(all)
        True

        The make_perm method of a PermutationGroup will randomly pick
        permutations, multiply them together, and return the permutation that
        can be applied to the polyhedron to give the orientation produced
        by those individual permutations.

        Here, 3 permutations are used:

        >>> tetra.pgroup.make_perm(3) # doctest: +SKIP
        Permutation([0, 3, 1, 2])

        To select the permutations that should be used, supply a list
        of indices to the permutations in pgroup in the order they should
        be applied:

        >>> use = [0, 0, 2]
        >>> p002 = tetra.pgroup.make_perm(3, use)
        >>> p002
        Permutation([1, 0, 3, 2])


        Apply them one at a time:

        >>> tetra.reset()
        >>> for i in use:
        ...     tetra.rotate(pgroup[i])
        ...
        >>> tetra.vertices
        (x, w, z, y)
        >>> sequentially = tetra.vertices

        Apply the composite permutation:

        >>> tetra.reset()
        >>> tetra.rotate(p002)
        >>> tetra.corners
        (x, w, z, y)
        >>> tetra.corners in all and tetra.corners == sequentially
        True

        Notes
        =====

        Defining permutation groups
        ---------------------------

        It is not necessary to enter any permutations, nor is necessary to
        enter a complete set of transformations. In fact, for a polyhedron,
        all configurations can be constructed from just two permutations.
        For example, the orientations of a tetrahedron can be generated from
        an axis passing through a vertex and face and another axis passing
        through a different vertex or from an axis passing through the
        midpoints of two edges opposite of each other.

        For simplicity of presentation, consider a square --
        not a cube -- with vertices 1, 2, 3, and 4:

        1-----2  We could think of axes of rotation being:
        |     |  1) through the face
        |     |  2) from midpoint 1-2 to 3-4 or 1-3 to 2-4
        3-----4  3) lines 1-4 or 2-3


        To determine how to write the permutations, imagine 4 cameras,
        one at each corner, labeled A-D:

        A       B          A       B
         1-----2            1-----3             vertex index:
         |     |            |     |                 1   0
         |     |            |     |                 2   1
         3-----4            2-----4                 3   2
        C       D          C       D                4   3

        original           after rotation
                           along 1-4

        A diagonal and a face axis will be chosen for the "permutation group"
        from which any orientation can be constructed.

        >>> pgroup = []

        Imagine a clockwise rotation when viewing 1-4 from camera A. The new
        orientation is (in camera-order): 1, 3, 2, 4 so the permutation is
        given using the *indices* of the vertices as:

        >>> pgroup.append(Permutation((0, 2, 1, 3)))

        Now imagine rotating clockwise when looking down an axis entering the
        center of the square as viewed. The new camera-order would be
        3, 1, 4, 2 so the permutation is (using indices):

        >>> pgroup.append(Permutation((2, 0, 3, 1)))

        The square can now be constructed:
            ** use real-world labels for the vertices, entering them in
               camera order
            ** for the faces we use zero-based indices of the vertices
               in *edge-order* as the face is traversed; neither the
               direction nor the starting point matter -- the faces are
               only used to define edges (if so desired).

        >>> square = Polyhedron((1, 2, 3, 4), [(0, 1, 3, 2)], pgroup)

        To rotate the square with a single permutation we can do:

        >>> square.rotate(square.pgroup[0])
        >>> square.corners
        (1, 3, 2, 4)

        To use more than one permutation (or to use one permutation more
        than once) it is more convenient to use the make_perm method:

        >>> p011 = square.pgroup.make_perm([0, 1, 1]) # diag flip + 2 rotations
        >>> square.reset() # return to initial orientation
        >>> square.rotate(p011)
        >>> square.corners
        (4, 2, 3, 1)

        Thinking outside the box
        ------------------------

        Although the Polyhedron object has a direct physical meaning, it
        actually has broader application. In the most general sense it is
        just a decorated PermutationGroup, allowing one to connect the
        permutations to something physical. For example, a Rubik's cube is
        not a proper polyhedron, but the Polyhedron class can be used to
        represent it in a way that helps to visualize the Rubik's cube.

        >>> from sympy.utilities.iterables import flatten, unflatten
        >>> from sympy import symbols
        >>> from sympy.combinatorics import RubikGroup
        >>> facelets = flatten([symbols(s+'1:5') for s in 'UFRBLD'])
        >>> def show():
        ...     pairs = unflatten(r2.corners, 2)
        ...     print(pairs[::2])
        ...     print(pairs[1::2])
        ...
        >>> r2 = Polyhedron(facelets, pgroup=RubikGroup(2))
        >>> show()
        [(U1, U2), (F1, F2), (R1, R2), (B1, B2), (L1, L2), (D1, D2)]
        [(U3, U4), (F3, F4), (R3, R4), (B3, B4), (L3, L4), (D3, D4)]
        >>> r2.rotate(0) # cw rotation of F
        >>> show()
        [(U1, U2), (F3, F1), (U3, R2), (B1, B2), (L1, D1), (R3, R1)]
        [(L4, L2), (F4, F2), (U4, R4), (B3, B4), (L3, D2), (D3, D4)]

        Predefined Polyhedra
        ====================

        For convenience, the vertices and faces are defined for the following
        standard solids along with a permutation group for transformations.
        When the polyhedron is oriented as indicated below, the vertices in
        a given horizontal plane are numbered in ccw direction, starting from
        the vertex that will give the lowest indices in a given face. (In the
        net of the vertices, indices preceded by "-" indicate replication of
        the lhs index in the net.)

        tetrahedron, tetrahedron_faces
        ------------------------------

            4 vertices (vertex up) net:

                 0 0-0
                1 2 3-1

            4 faces:

            (0, 1, 2) (0, 2, 3) (0, 3, 1) (1, 2, 3)

        cube, cube_faces
        ----------------

            8 vertices (face up) net:

                0 1 2 3-0
                4 5 6 7-4

            6 faces:

            (0, 1, 2, 3)
            (0, 1, 5, 4) (1, 2, 6, 5) (2, 3, 7, 6) (0, 3, 7, 4)
            (4, 5, 6, 7)

        octahedron, octahedron_faces
        ----------------------------

            6 vertices (vertex up) net:

                 0 0 0-0
                1 2 3 4-1
                 5 5 5-5

            8 faces:

            (0, 1, 2) (0, 2, 3) (0, 3, 4) (0, 1, 4)
            (1, 2, 5) (2, 3, 5) (3, 4, 5) (1, 4, 5)

        dodecahedron, dodecahedron_faces
        --------------------------------

            20 vertices (vertex up) net:

                  0  1  2  3  4 -0
                  5  6  7  8  9 -5
                14 10 11 12 13-14
                15 16 17 18 19-15

            12 faces:

            (0, 1, 2, 3, 4) (0, 1, 6, 10, 5) (1, 2, 7, 11, 6)
            (2, 3, 8, 12, 7) (3, 4, 9, 13, 8) (0, 4, 9, 14, 5)
            (5, 10, 16, 15, 14) (6, 10, 16, 17, 11) (7, 11, 17, 18, 12)
            (8, 12, 18, 19, 13) (9, 13, 19, 15, 14)(15, 16, 17, 18, 19)

        icosahedron, icosahedron_faces
        ------------------------------

            12 vertices (face up) net:

                 0  0  0  0 -0
                1  2  3  4  5 -1
                 6  7  8  9  10 -6
                  11 11 11 11 -11

            20 faces:

            (0, 1, 2) (0, 2, 3) (0, 3, 4)
            (0, 4, 5) (0, 1, 5) (1, 2, 6)
            (2, 3, 7) (3, 4, 8) (4, 5, 9)
            (1, 5, 10) (2, 6, 7) (3, 7, 8)
            (4, 8, 9) (5, 9, 10) (1, 6, 10)
            (6, 7, 11) (7, 8, 11) (8, 9, 11)
            (9, 10, 11) (6, 10, 11)

        >>> from sympy.combinatorics.polyhedron import cube
        >>> cube.edges
        {(0, 1), (0, 3), (0, 4), '...', (4, 7), (5, 6), (6, 7)}

        If you want to use letters or other names for the corners you
        can still use the pre-calculated faces:

        >>> corners = list('abcdefgh')
        >>> Polyhedron(corners, cube.faces).corners
        (a, b, c, d, e, f, g, h)

        References
        ==========

        .. [1] www.ocf.berkeley.edu/~wwu/articles/platonicsolids.pdf

        """
        # ... other code
```



#### Split 3
175 tokens, line: 383 - 394

```python
class Polyhedron(Basic):

    def __new__(cls, corners, faces=[], pgroup=[]):
        faces = [minlex(f, directed=False, is_set=True) for f in faces]
        corners, faces, pgroup = args = \
            [Tuple(*a) for a in (corners, faces, pgroup)]
        obj = Basic.__new__(cls, *args)
        obj._corners = tuple(corners)  # in order given
        obj._faces = FiniteSet(*faces)
        if pgroup and pgroup[0].size != len(corners):
            raise ValueError("Permutation size unequal to number of corners.")
        # use the identity permutation if none are given
        obj._pgroup = PermutationGroup((
            pgroup or [Perm(range(len(corners)))] ))
        return obj
```



#### Split 4
140 tokens, line: 396 - 418

```python
class Polyhedron(Basic):

    @property
    def corners(self):
        """
        Get the corners of the Polyhedron.

        The method ``vertices`` is an alias for ``corners``.

        Examples
        ========

        >>> from sympy.combinatorics import Polyhedron
        >>> from sympy.abc import a, b, c, d
        >>> p = Polyhedron(list('abcd'))
        >>> p.corners == p.vertices == (a, b, c, d)
        True

        See Also
        ========

        array_form, cyclic_form
        """
        return self._corners
    vertices = corners
```



#### Split 5
213 tokens, line: 420 - 447

```python
class Polyhedron(Basic):

    @property
    def array_form(self):
        """Return the indices of the corners.

        The indices are given relative to the original position of corners.

        Examples
        ========

        >>> from sympy.combinatorics import Permutation, Cycle
        >>> from sympy.combinatorics.polyhedron import tetrahedron
        >>> tetrahedron = tetrahedron.copy()
        >>> tetrahedron.array_form
        [0, 1, 2, 3]

        >>> tetrahedron.rotate(0)
        >>> tetrahedron.array_form
        [0, 2, 3, 1]
        >>> tetrahedron.pgroup[0].array_form
        [0, 2, 3, 1]

        See Also
        ========

        corners, cyclic_form
        """
        corners = list(self.args[0])
        return [corners.index(c) for c in self.corners]
```



#### Split 6
164 tokens, line: 449 - 481

```python
class Polyhedron(Basic):

    @property
    def cyclic_form(self):
        """Return the indices of the corners in cyclic notation.

        The indices are given relative to the original position of corners.

        See Also
        ========

        corners, array_form
        """
        return Perm._af_new(self.array_form).cyclic_form

    @property
    def size(self):
        """
        Get the number of corners of the Polyhedron.
        """
        return len(self._corners)

    @property
    def faces(self):
        """
        Get the faces of the Polyhedron.
        """
        return self._faces

    @property
    def pgroup(self):
        """
        Get the permutations of the Polyhedron.
        """
        return self._pgroup
```



#### Split 7
189 tokens, line: 483 - 506

```python
class Polyhedron(Basic):

    @property
    def edges(self):
        """
        Given the faces of the polyhedra we can get the edges.

        Examples
        ========

        >>> from sympy.combinatorics import Polyhedron
        >>> from sympy.abc import a, b, c
        >>> corners = (a, b, c)
        >>> faces = [(0, 1, 2)]
        >>> Polyhedron(corners, faces).edges
        {(0, 1), (0, 2), (1, 2)}

        """
        if self._edges is None:
            output = set()
            for face in self.faces:
                for i in range(len(face)):
                    edge = tuple(sorted([face[i], face[i - 1]]))
                    output.add(edge)
            self._edges = FiniteSet(*output)
        return self._edges
```



#### Split 8
621 tokens, line: 508 - 574

```python
class Polyhedron(Basic):

    def rotate(self, perm):
        """
        Apply a permutation to the polyhedron *in place*. The permutation
        may be given as a Permutation instance or an integer indicating
        which permutation from pgroup of the Polyhedron should be
        applied.

        This is an operation that is analogous to rotation about
        an axis by a fixed increment.

        Notes
        =====

        When a Permutation is applied, no check is done to see if that
        is a valid permutation for the Polyhedron. For example, a cube
        could be given a permutation which effectively swaps only 2
        vertices. A valid permutation (that rotates the object in a
        physical way) will be obtained if one only uses
        permutations from the ``pgroup`` of the Polyhedron. On the other
        hand, allowing arbitrary rotations (applications of permutations)
        gives a way to follow named elements rather than indices since
        Polyhedron allows vertices to be named while Permutation works
        only with indices.

        Examples
        ========

        >>> from sympy.combinatorics import Polyhedron, Permutation
        >>> from sympy.combinatorics.polyhedron import cube
        >>> cube = cube.copy()
        >>> cube.corners
        (0, 1, 2, 3, 4, 5, 6, 7)
        >>> cube.rotate(0)
        >>> cube.corners
        (1, 2, 3, 0, 5, 6, 7, 4)

        A non-physical "rotation" that is not prohibited by this method:

        >>> cube.reset()
        >>> cube.rotate(Permutation([[1, 2]], size=8))
        >>> cube.corners
        (0, 2, 1, 3, 4, 5, 6, 7)

        Polyhedron can be used to follow elements of set that are
        identified by letters instead of integers:

        >>> shadow = h5 = Polyhedron(list('abcde'))
        >>> p = Permutation([3, 0, 1, 2, 4])
        >>> h5.rotate(p)
        >>> h5.corners
        (d, a, b, c, e)
        >>> _ == shadow.corners
        True
        >>> copy = h5.copy()
        >>> h5.rotate(p)
        >>> h5.corners == copy.corners
        False
        """
        if not isinstance(perm, Perm):
            perm = self.pgroup[perm]
            # and we know it's valid
        else:
            if perm.size != self.size:
                raise ValueError('Polyhedron and Permutation sizes differ.')
        a = perm.array_form
        corners = [self.corners[a[i]] for i in range(len(self.corners))]
        self._corners = tuple(corners)
```



#### Split 9
137 tokens, line: 576 - 593

```python
class Polyhedron(Basic):

    def reset(self):
        """Return corners to their original positions.

        Examples
        ========

        >>> from sympy.combinatorics.polyhedron import tetrahedron as T
        >>> T = T.copy()
        >>> T.corners
        (0, 1, 2, 3)
        >>> T.rotate(0)
        >>> T.corners
        (0, 2, 3, 1)
        >>> T.reset()
        >>> T.corners
        (0, 1, 2, 3)
        """
        self._corners = self.args[0]
```



#### Split 10
277 tokens, line: 596 - 696

```python
def _pgroup_calcs():
    def _pgroup_of_double(polyh, ordered_faces, pgroup):
        n = len(ordered_faces[0])
        # the vertices of the double which sits inside a give polyhedron
        # can be found by tracking the faces of the outer polyhedron.
        # A map between face and the vertex of the double is made so that
        # after rotation the position of the vertices can be located
        fmap = dict(zip(ordered_faces,
                        range(len(ordered_faces))))
        flat_faces = flatten(ordered_faces)
        new_pgroup = []
        for i, p in enumerate(pgroup):
            h = polyh.copy()
            h.rotate(p)
            c = h.corners
            # reorder corners in the order they should appear when
            # enumerating the faces
            reorder = unflatten([c[j] for j in flat_faces], n)
            # make them canonical
            reorder = [tuple(map(as_int,
                       minlex(f, directed=False, is_set=True)))
                       for f in reorder]
            # map face to vertex: the resulting list of vertices are the
            # permutation that we seek for the double
            new_pgroup.append(Perm([fmap[f] for f in reorder]))
        return new_pgroup
    # ... other code
```



#### Split 11
397 tokens, line: 698 - 726

```python
def _pgroup_calcs():
    # ... other code

    tetrahedron_faces = [
        (0, 1, 2), (0, 2, 3), (0, 3, 1),  # upper 3
        (1, 2, 3),  # bottom
    ]

    # cw from top
    #
    _t_pgroup = [
        Perm([[1, 2, 3], [0]]),  # cw from top
        Perm([[0, 1, 2], [3]]),  # cw from front face
        Perm([[0, 3, 2], [1]]),  # cw from back right face
        Perm([[0, 3, 1], [2]]),  # cw from back left face
        Perm([[0, 1], [2, 3]]),  # through front left edge
        Perm([[0, 2], [1, 3]]),  # through front right edge
        Perm([[0, 3], [1, 2]]),  # through back edge
    ]

    tetrahedron = Polyhedron(
        range(4),
        tetrahedron_faces,
        _t_pgroup)

    cube_faces = [
        (0, 1, 2, 3),  # upper
        (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (0, 3, 7, 4),  # middle 4
        (4, 5, 6, 7),  # lower
    ]

    # U, D, F, B, L, R = up, down, front, back, left, right
    # ... other code
```



#### Split 12
613 tokens, line: 727 - 759

```python
def _pgroup_calcs():
    # ... other code
    _c_pgroup = [Perm(p) for p in
        [
        [1, 2, 3, 0, 5, 6, 7, 4],  # cw from top, U
        [4, 0, 3, 7, 5, 1, 2, 6],  # cw from F face
        [4, 5, 1, 0, 7, 6, 2, 3],  # cw from R face

        [1, 0, 4, 5, 2, 3, 7, 6],  # cw through UF edge
        [6, 2, 1, 5, 7, 3, 0, 4],  # cw through UR edge
        [6, 7, 3, 2, 5, 4, 0, 1],  # cw through UB edge
        [3, 7, 4, 0, 2, 6, 5, 1],  # cw through UL edge
        [4, 7, 6, 5, 0, 3, 2, 1],  # cw through FL edge
        [6, 5, 4, 7, 2, 1, 0, 3],  # cw through FR edge

        [0, 3, 7, 4, 1, 2, 6, 5],  # cw through UFL vertex
        [5, 1, 0, 4, 6, 2, 3, 7],  # cw through UFR vertex
        [5, 6, 2, 1, 4, 7, 3, 0],  # cw through UBR vertex
        [7, 4, 0, 3, 6, 5, 1, 2],  # cw through UBL
        ]]

    cube = Polyhedron(
        range(8),
        cube_faces,
        _c_pgroup)

    octahedron_faces = [
        (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 1, 4),  # top 4
        (1, 2, 5), (2, 3, 5), (3, 4, 5), (1, 4, 5),  # bottom 4
    ]

    octahedron = Polyhedron(
        range(6),
        octahedron_faces,
        _pgroup_of_double(cube, cube_faces, _c_pgroup))
    # ... other code
```



#### Split 13
694 tokens, line: 761 - 807

```python
def _pgroup_calcs():
    # ... other code

    dodecahedron_faces = [
        (0, 1, 2, 3, 4),  # top
        (0, 1, 6, 10, 5), (1, 2, 7, 11, 6), (2, 3, 8, 12, 7),  # upper 5
        (3, 4, 9, 13, 8), (0, 4, 9, 14, 5),
        (5, 10, 16, 15, 14), (6, 10, 16, 17, 11), (7, 11, 17, 18,
          12),  # lower 5
        (8, 12, 18, 19, 13), (9, 13, 19, 15, 14),
        (15, 16, 17, 18, 19)  # bottom
    ]

    def _string_to_perm(s):
        rv = [Perm(range(20))]
        p = None
        for si in s:
            if si not in '01':
                count = int(si) - 1
            else:
                count = 1
                if si == '0':
                    p = _f0
                elif si == '1':
                    p = _f1
            rv.extend([p]*count)
        return Perm.rmul(*rv)

    # top face cw
    _f0 = Perm([
        1, 2, 3, 4, 0, 6, 7, 8, 9, 5, 11,
        12, 13, 14, 10, 16, 17, 18, 19, 15])
    # front face cw
    _f1 = Perm([
        5, 0, 4, 9, 14, 10, 1, 3, 13, 15,
        6, 2, 8, 19, 16, 17, 11, 7, 12, 18])
    # the strings below, like 0104 are shorthand for F0*F1*F0**4 and are
    # the remaining 4 face rotations, 15 edge permutations, and the
    # 10 vertex rotations.
    _dodeca_pgroup = [_f0, _f1] + [_string_to_perm(s) for s in '''
    0104 140 014 0410
    010 1403 03104 04103 102
    120 1304 01303 021302 03130
    0412041 041204103 04120410 041204104 041204102
    10 01 1402 0140 04102 0412 1204 1302 0130 03120'''.strip().split()]

    dodecahedron = Polyhedron(
        range(20),
        dodecahedron_faces,
        _dodeca_pgroup)
    # ... other code
```



#### Split 14
316 tokens, line: 809 - 823

```python
def _pgroup_calcs():
    # ... other code

    icosahedron_faces = [
        (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 5), (0, 1, 5),
        (1, 6, 7), (1, 2, 7), (2, 7, 8), (2, 3, 8), (3, 8, 9),
        (3, 4, 9), (4, 9, 10), (4, 5, 10), (5, 6, 10), (1, 5, 6),
        (6, 7, 11), (7, 8, 11), (8, 9, 11), (9, 10, 11), (6, 10, 11)]

    icosahedron = Polyhedron(
        range(12),
        icosahedron_faces,
        _pgroup_of_double(
            dodecahedron, dodecahedron_faces, _dodeca_pgroup))

    return (tetrahedron, cube, octahedron, dodecahedron, icosahedron,
        tetrahedron_faces, cube_faces, octahedron_faces,
        dodecahedron_faces, icosahedron_faces)
```



#### Split 15
616 tokens, line: 825 - 871

```python
# -----------------------------------------------------------------------
#   Standard Polyhedron groups
#
#   These are generated using _pgroup_calcs() above. However to save
#   import time we encode them explicitly here.
# -----------------------------------------------------------------------

tetrahedron = Polyhedron(
    Tuple(0, 1, 2, 3),
    Tuple(
        Tuple(0, 1, 2),
        Tuple(0, 2, 3),
        Tuple(0, 1, 3),
        Tuple(1, 2, 3)),
    Tuple(
        Perm(1, 2, 3),
        Perm(3)(0, 1, 2),
        Perm(0, 3, 2),
        Perm(0, 3, 1),
        Perm(0, 1)(2, 3),
        Perm(0, 2)(1, 3),
        Perm(0, 3)(1, 2)
    ))

cube = Polyhedron(
    Tuple(0, 1, 2, 3, 4, 5, 6, 7),
    Tuple(
        Tuple(0, 1, 2, 3),
        Tuple(0, 1, 5, 4),
        Tuple(1, 2, 6, 5),
        Tuple(2, 3, 7, 6),
        Tuple(0, 3, 7, 4),
        Tuple(4, 5, 6, 7)),
    Tuple(
        Perm(0, 1, 2, 3)(4, 5, 6, 7),
        Perm(0, 4, 5, 1)(2, 3, 7, 6),
        Perm(0, 4, 7, 3)(1, 5, 6, 2),
        Perm(0, 1)(2, 4)(3, 5)(6, 7),
        Perm(0, 6)(1, 2)(3, 5)(4, 7),
        Perm(0, 6)(1, 7)(2, 3)(4, 5),
        Perm(0, 3)(1, 7)(2, 4)(5, 6),
        Perm(0, 4)(1, 7)(2, 6)(3, 5),
        Perm(0, 6)(1, 5)(2, 4)(3, 7),
        Perm(1, 3, 4)(2, 7, 5),
        Perm(7)(0, 5, 2)(3, 4, 6),
        Perm(0, 5, 7)(1, 6, 3),
        Perm(0, 7, 2)(1, 4, 6)))
```



#### Split 16
361 tokens, line: 873 - 945

```python
octahedron = Polyhedron(
    Tuple(0, 1, 2, 3, 4, 5),
    Tuple(
        Tuple(0, 1, 2),
        Tuple(0, 2, 3),
        Tuple(0, 3, 4),
        Tuple(0, 1, 4),
        Tuple(1, 2, 5),
        Tuple(2, 3, 5),
        Tuple(3, 4, 5),
        Tuple(1, 4, 5)),
    Tuple(
        Perm(5)(1, 2, 3, 4),
        Perm(0, 4, 5, 2),
        Perm(0, 1, 5, 3),
        Perm(0, 1)(2, 4)(3, 5),
        Perm(0, 2)(1, 3)(4, 5),
        Perm(0, 3)(1, 5)(2, 4),
        Perm(0, 4)(1, 3)(2, 5),
        Perm(0, 5)(1, 4)(2, 3),
        Perm(0, 5)(1, 2)(3, 4),
        Perm(0, 4, 1)(2, 3, 5),
        Perm(0, 1, 2)(3, 4, 5),
        Perm(0, 2, 3)(1, 5, 4),
        Perm(0, 4, 3)(1, 5, 2)))

dodecahedron =
 # ... other code
```



#### Split 17
1398 tokens, line: 947 - 1012

```python
icosahedron = Polyhedron(
    Tuple(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),
    Tuple(
        Tuple(0, 1, 2),
        Tuple(0, 2, 3),
        Tuple(0, 3, 4),
        Tuple(0, 4, 5),
        Tuple(0, 1, 5),
        Tuple(1, 6, 7),
        Tuple(1, 2, 7),
        Tuple(2, 7, 8),
        Tuple(2, 3, 8),
        Tuple(3, 8, 9),
        Tuple(3, 4, 9),
        Tuple(4, 9, 10),
        Tuple(4, 5, 10),
        Tuple(5, 6, 10),
        Tuple(1, 5, 6),
        Tuple(6, 7, 11),
        Tuple(7, 8, 11),
        Tuple(8, 9, 11),
        Tuple(9, 10, 11),
        Tuple(6, 10, 11)),
    Tuple(
        Perm(11)(1, 2, 3, 4, 5)(6, 7, 8, 9, 10),
        Perm(0, 5, 6, 7, 2)(3, 4, 10, 11, 8),
        Perm(0, 1, 7, 8, 3)(4, 5, 6, 11, 9),
        Perm(0, 2, 8, 9, 4)(1, 7, 11, 10, 5),
        Perm(0, 3, 9, 10, 5)(1, 2, 8, 11, 6),
        Perm(0, 4, 10, 6, 1)(2, 3, 9, 11, 7),
        Perm(0, 1)(2, 5)(3, 6)(4, 7)(8, 10)(9, 11),
        Perm(0, 2)(1, 3)(4, 7)(5, 8)(6, 9)(10, 11),
        Perm(0, 3)(1, 9)(2, 4)(5, 8)(6, 11)(7, 10),
        Perm(0, 4)(1, 9)(2, 10)(3, 5)(6, 8)(7, 11),
        Perm(0, 5)(1, 4)(2, 10)(3, 6)(7, 9)(8, 11),
        Perm(0, 6)(1, 5)(2, 10)(3, 11)(4, 7)(8, 9),
        Perm(0, 7)(1, 2)(3, 6)(4, 11)(5, 8)(9, 10),
        Perm(0, 8)(1, 9)(2, 3)(4, 7)(5, 11)(6, 10),
        Perm(0, 9)(1, 11)(2, 10)(3, 4)(5, 8)(6, 7),
        Perm(0, 10)(1, 9)(2, 11)(3, 6)(4, 5)(7, 8),
        Perm(0, 11)(1, 6)(2, 10)(3, 9)(4, 8)(5, 7),
        Perm(0, 11)(1, 8)(2, 7)(3, 6)(4, 10)(5, 9),
        Perm(0, 11)(1, 10)(2, 9)(3, 8)(4, 7)(5, 6),
        Perm(0, 11)(1, 7)(2, 6)(3, 10)(4, 9)(5, 8),
        Perm(0, 11)(1, 9)(2, 8)(3, 7)(4, 6)(5, 10),
        Perm(0, 5, 1)(2, 4, 6)(3, 10, 7)(8, 9, 11),
        Perm(0, 1, 2)(3, 5, 7)(4, 6, 8)(9, 10, 11),
        Perm(0, 2, 3)(1, 8, 4)(5, 7, 9)(6, 11, 10),
        Perm(0, 3, 4)(1, 8, 10)(2, 9, 5)(6, 7, 11),
        Perm(0, 4, 5)(1, 3, 10)(2, 9, 6)(7, 8, 11),
        Perm(0, 10, 7)(1, 5, 6)(2, 4, 11)(3, 9, 8),
        Perm(0, 6, 8)(1, 7, 2)(3, 5, 11)(4, 10, 9),
        Perm(0, 7, 9)(1, 11, 4)(2, 8, 3)(5, 6, 10),
        Perm(0, 8, 10)(1, 7, 6)(2, 11, 5)(3, 9, 4),
        Perm(0, 9, 6)(1, 3, 11)(2, 8, 7)(4, 10, 5)))

tetrahedron_faces = list(tuple(arg) for arg in tetrahedron.faces)

cube_faces = list(tuple(arg) for arg in cube.faces)

octahedron_faces = list(tuple(arg) for arg in octahedron.faces)

dodecahedron_faces = list(tuple(arg) for arg in dodecahedron.faces)

icosahedron_faces = list(tuple(arg) for arg in icosahedron.faces)
```

