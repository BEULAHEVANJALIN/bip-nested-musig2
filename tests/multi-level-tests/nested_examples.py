from tree import *
from nested_musig2_exec import simulate_sign_test

tree1 = parse_forest("0(17(21(11(0(13(18)))),22(9(8(7,14(6(19)),12(1(4(2(3(15,16(5(10,20))))))))))))")
simulate_sign_test(tree1)

tree2 = parse_forest("4(5,0(6),2(7(3,8(1),9)))")
simulate_sign_test(tree2)
