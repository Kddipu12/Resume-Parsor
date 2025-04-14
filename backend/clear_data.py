import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('resumes.db')
c = conn.cursor()

# Delete all records from the resumes and jobs tables
c.execute('DELETE FROM resumes')
c.execute('DELETE FROM jobs')

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Data cleared from resumes and jobs tables.")
