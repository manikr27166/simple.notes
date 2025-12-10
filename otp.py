#H6sV5f

import random
def genotp():
    otp=''
    for i in range(2):
        a=random.randint(65,91)
        b=random.randint(0,9)
        c=random.randint(97,123)
        otp = otp + chr(a) + str(b) + chr(c)
    return otp
genotp()