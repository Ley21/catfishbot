from tortoise.models import Model
from tortoise import fields


class Race(Model):
    id = fields.IntField(pk=True)
    preset = fields.TextField()
    seed = fields.TextField()
    date = fields.DatetimeField
    ongoing = fields.BooleanField(default=True)
    author_id = fields.IntField()
    author = fields.TextField()

    def __str__(self):
        return self.id


class Participant(Model):
    race = fields.ForeignKeyField('models.Race')
    player_id = fields.IntField()
    player = fields.TextField()
    end_time = fields.DatetimeField

    class Meta:
        unique_together = ("race", "player_id")

    def __str__(self):
        return f"{self.race_id}_{self.name}"
