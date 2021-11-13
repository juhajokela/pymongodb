import mongodb as db


db.connection('mongodb://jkl:123qwerasdfzxcvjkl890@ds125272.mlab.com:25272/forms-db')


class Person(db.Model):
    name = db.StringField(length_min=1)
    age = db.IntegerField(value_min=0)


'''
person = Person.create(name='Juha Jokela', age=28)
print(person)
'''
