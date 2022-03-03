class Vector:
    test: any
    expect: any

    def __init__(self, test, expect) -> None:
        self.test = test
        self.expect = expect


class VectorFailure(Exception):
    def __init__(self, test: Vector, got) -> None:
        super().__init__(
            f'TEST {test.test} \n'
            f'EXPECT {test.expect} \n'
            f'GOT {got}'
        )
