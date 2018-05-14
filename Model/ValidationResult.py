class ValidationResult:

    def __init__(self):
        self.valid = None
        self.error_msgs = []

    def add_error_msg(self, msg):
        self.error_msgs.append(msg)

    def set_valid(self, boolean):
        self.valid = boolean

    def is_valid(self):
        return self.valid

    def error_count(self):
        return len(self.error_msgs)

    def error_list(self):
        return self.error_msgs

    def get_errors(self):
        ret_val = ""
        if len(self.error_msgs) > 0:
            ret_val = "\n".join(self.error_msgs)
        else:
            ret_val = "No error messages"
        return ret_val
