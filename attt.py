

def dich_caesar(chuoi, do_dich):
   
    k = do_dich % 26
    ket_qua = []

    for ky_tu in chuoi:
        if 'A' <= ky_tu <= 'Z':
            moc = ord('A')
            ket_qua.append(chr((ord(ky_tu) - moc + k) % 26 + moc))
        elif 'a' <= ky_tu <= 'z':
            moc = ord('a')
            ket_qua.append(chr((ord(ky_tu) - moc + k) % 26 + moc))
        else:
            ket_qua.append(ky_tu)

    return ''.join(ket_qua)


def ma_hoa(van_ban, khoa):
    return dich_caesar(van_ban, khoa)
def giai_ma(ban_ma, khoa):
    return dich_caesar(ban_ma, -khoa)
def nhap_khoa():
    while True:
        try:
            return int(input("Nhap khoa K: "))
        except ValueError:
            print("K phai la mot so nguyen. Vui long nhap lai!")
def main():
    while True:
        print("\n===== CHUONG TRINH CAESAR =====")
        print("1. Ma hoa")
        print("2. Giai ma")
        print("0. Thoat")

        lua_chon = input("Chon chuc nang: ").strip()

        if lua_chon == '1':
            van_ban = input("Nhap xau can ma hoa: ")
            khoa = nhap_khoa()
            print("Ban ma:", ma_hoa(van_ban, khoa))

        elif lua_chon == '2':
            ban_ma = input("Nhap ban ma can giai ma: ")
            khoa = nhap_khoa()
            print("Ban ro:", giai_ma(ban_ma, khoa))

        elif lua_chon == '0':
            print("Ket thuc chuong trinh.")
            break

        else:
            print("Lua chon khong hop le. Hay chon 0, 1 hoac 2.")


if __name__ == '__main__':
    main()
