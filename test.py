from pprint import pprint
from random import sample

from computation import Shamir_Secret_Sharing

def test(shares, secret, mod):
    summation = sum(shares) % mod
    assert(summation == secret)

if __name__ == '__main__':
    t = 5
    secret_sharing = Shamir_Secret_Sharing(10, t)
    secret = 100000
    shares = secret_sharing.gen_shares(secret)
    print(secret)
    pprint(shares)
    print()
    gen_from_shares = sample(shares, t)
    regenerated_secret = secret_sharing.regenerate(gen_from_shares, 'DEBUG')
    print(regenerated_secret)
    assert(secret == regenerated_secret)