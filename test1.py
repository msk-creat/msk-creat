
#变量
print(0b100)  # 二进制整数
print(0o100)  # 八进制整数
print(100)    # 十进制整数
print(0x100)  # 十六进制整数
#浮点型
print(123.456)    # 数学写法
print(1.23456e2)  # 科学计数法
#字符串类型
print("hello world")
#Bool类型
print(True)

a = 100
b = 123.45
c = 'hello, world'
d = True
e='123'
f='100'
g='123.45'
print(type(a))  # <class 'int'>
print(type(b))  # <class 'float'>
print(type(c))  # <class 'str'>
print(type(d))  # <class 'bool'>
#type检查变量类型
print(float(a))        
print(int(b))           
print(int(d))           
print(int(e, base=16)) 
print(int(e, base=10))   
print(float(e))        
print(bool(c))          
print(int(f))          
print(chr(a))          
print(ord('e'))  
print(f"{a:.3f}") 
print(str(d).encode("gbk"))      
#海象运算符
# print(a:=10)#print(a=10)会报错
# f=float(input())
# c=23
#print("%.1fand%.2f"%(f,c))
str1="qazwsx"
str2="wsxedc"
str1=str1.replace(str1,str2)
print(str1)
set1={1,2,3,4,(1,3)}
set2={0,3,5,4,1}
print(set1^set2)
dic={"1":1,"2":2}
print(dic.pop("1"))