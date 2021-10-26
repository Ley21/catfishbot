from tortoise.models import Model
from tortoise import fields
from datetime import timedelta

class Race(Model):
    id = fields.IntField(pk=True)
    preset = fields.TextField()
    seed = fields.TextField(default="")
    date = fields.DatetimeField()
    open = fields.BooleanField(default=True)
    ongoing = fields.BooleanField(default=False)
    finished = fields.BooleanField(default=False)
    author_id = fields.IntField()
    author = fields.TextField()
    guild = fields.IntField()

    def __str__(self):
        return self.id


class Participant(Model):
    race = fields.ForeignKeyField('models.Race')
    player_id = fields.IntField()
    player = fields.TextField()
    end_time = fields.DatetimeField
    time = fields.TimeDeltaField(default=timedelta(hours=99))
    resign = fields.BooleanField(default=False)

    class Meta:
        unique_together = ("race", "player_id")

    def __str__(self):
        return f"{self.id}_{self.player}"


class GuildSettings(Model):
    guild = fields.IntField(pk=True)
    race_registration_channel_id = fields.IntField()
    race_chat_channel_id = fields.IntField()
    race_channel_id = fields.IntField()
    race_result_channel_id = fields.IntField()
    race_active_role = fields.IntField()
    race_finish_role = fields.IntField()

    def __str__(self):
        return self.guild
