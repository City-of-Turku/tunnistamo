from .opas import OpasADFS

class OpasStudentADFS(OpasADFS):
    name = 'opas_student_adfs'

    def auth_allowed(self, response, details):
        role = details['school_role']
        if role == 'student':
            super().auth_allowed(response, details)
        else:
            return False