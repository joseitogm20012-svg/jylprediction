def suma(a, b):
    return a + b

def resta(a, b):
    return a - b

def multiplica(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "error"
    return a / b

def test_suma():
    assert suma(2, 3) == 5
    assert suma(-1, 1) == 0
    print("  [PASS] suma")

def test_resta():
    assert resta(5, 3) == 2
    assert resta(10, 7) == 3
    print("  [PASS] resta")

def test_multiplica():
    assert multiplica(3, 4) == 12
    assert multiplica(0, 5) == 0
    print("  [PASS] multiplica")

def test_divide():
    assert divide(10, 2) == 5
    assert divide(5, 0) == "error"
    print("  [PASS] divide")

if __name__ == "__main__":
    test_suma()
    test_resta()
    test_multiplica()
    test_divide()
    print("  Todos los tests pasaron!")
