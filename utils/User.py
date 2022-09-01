class User:
    def __init__(self, uid, nickname):
        self.id = int(uid)
        self.name = nickname

    def add2blacklist(self):
        # if self.id not in BLACK_LIST and self.id != 1584784496:
        #     BLACK_LIST.append(self.id)
        return

    def remove4blacklist(self):
        # BLACK_LIST.remove(self.id)
        return

    def isblack(self):
        # return self.id in BLACK_LIST
        return

    def isadmin(self):
        # return self.id in ADMIN_LIST
        return False

    def add2admin(self):
        # if self.id not in ADMIN_LIST:
        #     ADMIN_LIST.append(self.id)
        return

    def remove4admin(self):
        # if self.id != 1584784496:
        #     ADMIN_LIST.remove(self.id)
        return

    def __str__(self):
        return f"{self.name}({self.id})"
