"""타입 힌팅과 제네릭 - 수업 핵심 예제 모음 (메인 파일)

대구과학고 정보과학 / 객체지향 프로그래밍
수업 자료(oop_타입힌팅_제네릭_수업자료.html)에 나오는 예제를 한 파일에 모았다.

실행:  python typing_lesson_main.py
검사:  mypy --strict typing_lesson_main.py      # 오류 0개여야 한다
       (Python 3.12 이상 필요: def f[T](...) / class C[T] 문법 사용)

각 절은 [상황 주석] -> [코드] -> demo_*() -> test_*() 순서로 구성했다.
"의도된 오류 실험"은 맨 아래 주석에 모아 두었다. 주석을 풀고 mypy 로 확인해 보자.
"""
import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, Self


# ==============================================================
# 2. 타입 힌트 어휘
# 상황: 센서 로그를 처리하는 도구. 벡터, (시각, 값) 쌍, 값의 목록, 변환 함수, 열기 모드를 다룬다.
# 설계: 각각을 정확한 힌트로 적는다. 인자는 넓게(Sequence), 반환은 구체적으로(list).
# ==============================================================
Vector3 = tuple[float, float, float]      # 별칭: 길이가 3인 튜플
Reading = tuple[float, float]             # (측정 시각, 측정값)


def norm(v: Vector3) -> float:
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)      # list 도 tuple 도 받는다


def parse_line(line: str) -> Reading | None:
    parts = line.split(",")
    if len(parts) != 2:
        return None                       # 형식이 틀린 줄은 None
    return float(parts[0]), float(parts[1])


def apply(fn: Callable[[float], float], values: Iterable[float]) -> list[float]:
    return [fn(v) for v in values]


def open_log(mode: Literal["r", "w"]) -> str:
    return f"로그를 '{mode}' 모드로 연다"


def demo_vocab() -> None:
    print(norm((3.0, 4.0, 0.0)))
    print(mean([1, 2, 3]), mean((1.0, 2.0)))       # int 는 float 자리에 쓸 수 있다
    print(parse_line("0.5,21.3"), parse_line("깨진 줄"))
    print(apply(lambda x: x / 2, [1.0, 2.5]))
    print(open_log("r"))


def test_vocab() -> None:
    assert norm((3.0, 4.0, 0.0)) == 5.0
    assert mean([1, 2, 3]) == 2.0
    assert parse_line("0.5,21.3") == (0.5, 21.3)
    assert parse_line("깨진 줄") is None
    assert apply(lambda x: x / 2, [1.0, 2.5]) == [0.5, 1.25]


# ==============================================================
# 3. None 과 타입 좁히기
# 상황: 센서마다 보정 계수가 등록되어 있다. 등록되지 않은 센서가 들어오면?
# 설계: dict.get() 은 float | None 을 돌려준다. None 을 먼저 처리하고 벗어나면
#       그 아래에서 factor 는 float 로 좁혀진다. (not factor 는 0.0 도 걸러 버리니 쓰지 않는다)
# ==============================================================
CALIBRATION: dict[str, float] = {"temp": 0.98, "press": 1.02, "offset": 0.0}


def corrected(sensor: str, raw: float) -> float:
    factor = CALIBRATION.get(sensor)      # float | None
    if factor is None:
        raise KeyError(f"보정 계수가 없는 센서: {sensor}")
    return raw * factor                   # 여기서 factor 는 float


def to_meters(value: float | str) -> float:
    if isinstance(value, str):            # 이 안에서 value 는 str
        return float(value.rstrip("m"))
    return value                          # 여기서는 float


def demo_narrowing() -> None:
    print(corrected("temp", 100.0), corrected("offset", 100.0))
    print(to_meters("2.5m"), to_meters(3.0))


def test_narrowing() -> None:
    assert corrected("offset", 100.0) == 0.0      # 0.0 은 등록된 유효한 값이다
    try:
        corrected("humid", 100.0)
    except KeyError:
        pass
    else:
        raise AssertionError("등록되지 않은 센서는 KeyError 여야 한다")
    assert to_meters("2.5m") == 2.5


# ==============================================================
# 4. dataclass 와 Self
# 상황: 입자 시뮬레이션의 입자. 이름, 질량, 위치, 태그를 갖고, 이동 결과를 이어 붙일 수 있다.
# 설계: 필드 타입을 선언하는 @dataclass. 태그처럼 가변 기본값은 default_factory 로 만든다.
#       moved() 는 자기 자신을 돌려주므로 반환 타입을 Self 로 적는다.
# ==============================================================
@dataclass
class Particle:
    name: str
    mass: float
    position: Vector3 = (0.0, 0.0, 0.0)
    tags: list[str] = field(default_factory=list)

    def moved(self, dx: float, dy: float, dz: float) -> Self:
        x, y, z = self.position
        self.position = (x + dx, y + dy, z + dz)
        return self


def demo_particle() -> None:
    p = Particle("전자", 9.1e-31).moved(1.0, 0.0, 0.0).moved(0.0, 2.0, 0.0)
    print(p)
    print(Particle.__annotations__)       # dataclass 는 이 힌트를 읽어 __init__ 을 만든다


def test_particle() -> None:
    p = Particle("전자", 9.1e-31).moved(1.0, 0.0, 0.0).moved(0.0, 2.0, 0.0)
    assert p.position == (1.0, 2.0, 0.0)
    assert Particle("a", 1.0).tags is not Particle("b", 1.0).tags   # 입자마다 따로 갖는다


# ==============================================================
# 5. 제네릭 함수
# 상황: 목록의 첫 원소를 꺼내는 범용 함수. 온도 목록에도, 센서 이름 목록에도 쓰고 싶다.
# 설계: list[Any] 는 입력과 출력의 관계를 잃는다. 타입 변수 T 로 "같은 T 는 같은 타입"을 적는다.
# ==============================================================
def first[T](xs: Sequence[T]) -> T:
    return xs[0]


def demo_generic_function() -> None:
    print(first([21.5, 22.0]), first(("온도", "압력")))


def test_generic_function() -> None:
    assert first([21.5, 22.0]) == 21.5
    assert first("abc") == "a"


# ==============================================================
# 6. 제네릭 클래스
# 상황: 실험 단계 이름(str)을 쌓는 undo 스택과, 최근 측정값(float) 버퍼. 구조는 같고 원소 타입만 다르다.
# 설계: 원소 타입을 매개변수 T 로 둔 Stack[T]. 사용하는 쪽에서 Stack[str], Stack[float] 로 채운다.
#       비어 있음은 peek() 에서는 None(정상), pop() 에서는 예외(호출자의 실수)로 다르게 다룬다.
# ==============================================================
class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("빈 스택에서 pop 했습니다")
        return self._items.pop()

    def peek(self) -> T | None:
        return self._items[-1] if self._items else None

    def __len__(self) -> int:
        return len(self._items)


def demo_stack() -> None:
    undo: Stack[str] = Stack()
    undo.push("가열")
    undo.push("교반")
    top = undo.peek()
    if top is not None:                   # peek() 는 None 일 수 있으므로 좁힌 뒤에 쓴다
        print(top.upper())
    print(undo.pop(), len(undo))
    buffer: Stack[float] = Stack()
    buffer.push(21.5)


def test_stack() -> None:
    s: Stack[int] = Stack()
    assert s.peek() is None
    s.push(1)
    s.push(2)
    assert s.pop() == 2 and len(s) == 1
    s.pop()
    try:
        s.pop()
    except IndexError:
        pass
    else:
        raise AssertionError("빈 스택 pop 은 IndexError 여야 한다")


# ==============================================================
# 7. 제한된 타입 변수 (bound / constraint)
# 상황: 어떤 타입이든 받아 가장 큰 것을 찾고 싶다. 단, 원소끼리 < 로 비교할 수는 있어야 한다.
# 설계: "< 를 지원한다"를 Protocol 로 적고 T 의 bound 로 건다. (상속이 아니라 메서드로 판단 = 구조적 타이핑)
#       str 과 bytes 처럼 몇 가지 타입 중 하나로 고정하고 싶을 때는 constraint 를 쓴다.
# ==============================================================
class SupportsLessThan(Protocol):
    def __lt__(self, other: Any, /) -> bool: ...


def largest[T: SupportsLessThan](items: Sequence[T]) -> T:
    best = items[0]
    for x in items[1:]:
        if best < x:
            best = x
    return best


def concat[S: (str, bytes)](a: S, b: S) -> S:
    return a + b


def demo_bound() -> None:
    print(largest([3, 9, 4]), largest(["b", "z", "a"]))
    print(concat("a", "b"), concat(b"a", b"b"))


def test_bound() -> None:
    assert largest([3, 9, 4]) == 9
    assert largest(["b", "z", "a"]) == "z"
    assert concat("a", "b") == "ab"
    assert concat(b"a", b"b") == b"ab"


# ==============================================================
# 8. 공변과 불변
# 상황: 고양이 목록(list[Cat])을 "동물 목록을 받는 함수"에 넘기고 싶다.
# 설계: 읽기만 하는 함수는 Sequence[Animal] 로 받으면 하위 타입 목록도 받는다(공변).
#       list[Animal] 로 받으면 함수가 목록에 Animal 을 끼워 넣을 수 있어서 거부된다(불변).
# ==============================================================
class Animal:
    def __init__(self, name: str) -> None:
        self.name = name


class Cat(Animal):
    def purr(self) -> str:
        return f"{self.name}: 가르릉"


def names(shelter: Sequence[Animal]) -> list[str]:
    return [a.name for a in shelter]


def demo_variance() -> None:
    cats: list[Cat] = [Cat("나비"), Cat("치즈")]
    print(names(cats))                    # list[Cat] 를 Sequence[Animal] 자리에 넘길 수 있다


def test_variance() -> None:
    cats: list[Cat] = [Cat("나비")]
    assert names(cats) == ["나비"]


# ==============================================================
# 의도된 오류 실험 - 아래 줄의 주석을 풀고 mypy --strict 를 실행해 보자.
# (실행 결과는 수업 자료에서 확인한 mypy 2.3.1 기준이며, 버전에 따라 문구가 조금 다를 수 있다)
#
#   open_log("a")                  # arg-type: "Literal['a']" 는 Literal['r', 'w'] 가 아니다
#   norm((1.0, 2.0))               # arg-type: 길이 2 튜플은 tuple[float, float, float] 가 아니다
#   Stack[str]().push(3)           # arg-type: "int" 는 "str" 자리에 올 수 없다
#   Stack[str]().peek().upper()    # union-attr: peek() 는 None 일 수 있다
#   largest([object(), object()])  # type-var: T 는 "object" 일 수 없다
#   concat(1, 2)                   # type-var: S 는 "int" 일 수 없다
#   def register(shelter: list[Animal]) -> None: ...
#   register([Cat("나비")])         # 리스트 리터럴은 통과한다 - 아래처럼 변수로 넘기면 거부된다
#   c: list[Cat] = [Cat("나비")]
#   register(c)                    # arg-type: "list[Cat]" 는 "list[Animal]" 자리에 올 수 없다 (불변)
# ==============================================================
def run_all() -> None:
    demo_vocab()
    demo_narrowing()
    demo_particle()
    demo_generic_function()
    demo_stack()
    demo_bound()
    demo_variance()
    test_vocab()
    test_narrowing()
    test_particle()
    test_generic_function()
    test_stack()
    test_bound()
    test_variance()
    print("모든 test 통과")


if __name__ == "__main__":
    run_all()
