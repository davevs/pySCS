# Control frameworks to use
Controls = {}

# add controllists
addControlList('test_sample.csv')
addControlList('test_sample2.csv')
# addControlList('default.csv')
# addControlList('gdpr.csv')

scs = SCS("my first model")
scs.description = "sample to show pySCS"

User_Web = Boundary("User/Web")

scs.process()