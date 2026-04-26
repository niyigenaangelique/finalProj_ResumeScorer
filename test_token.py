from database import ResumeDatabase
db = ResumeDatabase()
token = 'gm4p9obxkIT8Z_phFi41V6njwr7K9qCYH-ddWUbW4uM'
invite = db.get_invite_by_token(token)
print(f"Invite: {invite}")
