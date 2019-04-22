# Control frameworks to use
Controls = {}

# add controllists
import_control_list('test_sample.csv')
import_control_list('test_sample2.csv')
# import_control_list('default.csv')
# import_control_list('gdpr.csv')

scs = SCS("my first model")
scs.description = "sample to show pySCS"

User_Web = Boundary("User/Web")

scs.process()