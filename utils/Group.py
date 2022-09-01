class Group:
    def __init__(self, gid):
        self.id = int(gid)

    def get_users(self):
        # return getGroupUser(self.id)
        return

    def mute(self, user, mute_time):
        # mutePerson(self.id, user.id, mute_time)
        return

    def isverify(self):
        # if str(self.id) in VERIFIED:
        #     return True
        # return False
        return True

    def verify_info(self):
        # if str(self.id) in VERIFIED:
        #     return f"已验证 绑定邮箱:{''.join(VERIFIED[str(self.id)][0:3])}{len(VERIFIED[str(self.id)][3:-3]) * '*'}{''.join(VERIFIED[str(self.id)][-3:])}"
        # elif str(self.id) in VERIFYING:
        #     return f"正在验证..."
        # else:
        #     return f"未验证! 请使用 !mail 指令查看如何激活"
        return ""
