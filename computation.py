from os import urandom
from decimal import Decimal
from tinyec.ec import Curve, SubGroup, Point

rand_num = lambda: int(urandom(5).hex(), 16) % 10007

p = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f
n = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
a = 0x0
b = 0x7
G = (0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798, 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8)
h = 0x1
name = 'secp256k1'

class Shamir_Secret_Sharing:
    def __init__(self, n, t):
        self.n = n
        self.t = t

    def polynomial_coefficients(self, secret):
        return [rand_num() for _ in range(self.t - 1)] + [secret]
    
    def get_point(self, x):
        coeffs = self.coefficients
        # print(coeffs)
        y = 0
        for i in range(len(coeffs)):
            y += (x ** (len(coeffs) - 1 - i)) * coeffs[i]
        return y
    
    def gen_shares(self, secret):
        self.coefficients = self.polynomial_coefficients(secret)
        shares = []
        for _ in range(self.n):
            x = rand_num()
            y = self.get_point(x)
            shares.append((x, y))
        return shares

    def gen_shares_with_x_points(self, secret, x_points):
        self.coefficients = self.polynomial_coefficients(secret)
        shares = []
        for i in range(self.n):
            y = self.get_point(x_points[i])
            shares.append((x_points[i], y))
        return shares
    
    def regenerate(self, gen_from_shares, mode='QUIET'):
        sum = 0
        for idx, share in enumerate(gen_from_shares):
            prod = Decimal(1)
            for idx2, share2 in enumerate(gen_from_shares):
                if idx != idx2:
                    # print(share, share2)
                    temp = Decimal(str(Decimal(str(share2[0])) / (share2[0] - share[0])))
                    if mode == 'DEBUG':
                        print(temp)
                    prod = prod * temp
            prod = prod * Decimal(str(share[1]))
            sum = sum + Decimal(str(prod))
        # print(int(round(Decimal(str(sum)))))
        return int(round(Decimal(str(sum))))

def generate_shares(value, n, p):
    shares = []
    for i in range(n - 1):
        shares.append(rand_num() % p)
    shares.append(((value % p) - (sum(shares) % p)) % p)
    return shares

def sum_shares(shares, p):
    return sum(shares) % p

def ECC(private_key):
    curve = Curve(a, b, SubGroup(p, G, n, h), name)
    public_key_point = private_key * curve.g
    # public_key = '0' + str(2 + (public_key_point.y % 2)) + str(hex(public_key_point.x)[2:])
    # print(private_key, public_key, sep=' ')
    # return public_key
    return public_key_point

def compress_public_key(x, y):
    return '0' + str(2 + (y % 2)) + str(hex(x)[2:])

def coords_to_point(x, y):
    curve = Curve(a, b, SubGroup(p, G, n, h), name)
    return Point(curve, x, y)