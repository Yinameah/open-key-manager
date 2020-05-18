class M:
    M_attribute = 0

    @staticmethod
    def static_method():
        print("do a bunch of stuff")

    @classmethod
    def class_method(cls):
        print(cls)
        cls.M_attribute += 1
        print(cls.M_attribute)


m = M()

m.static_method()
M.static_method()

m.class_method()
M.class_method()
