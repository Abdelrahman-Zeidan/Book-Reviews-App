import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR NOT NULL, password VARCHAR NOT NULL)")
    db.execute("CREATE TABLE reviews (isbn VARCHAR NOT NULL, review VARCHAR NOT NULL, rating INTEGER NOT NULL, username VARCHAR NOT NULL)")
    db.execute("CREATE TABLE books (isbn VARCHAR PRIMARY KEY, title VARCHAR NOT NULL, author VARCHAR NOT NULL, year VARCHAR NOT NULL)")
    
    f = open("books.csv")
    reader = csv.reader(f)

    for isbn, title, author, year in reader:
        if year == "year":
            print("Skipped The first line which has the column names")
        else:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                         {"isbn": isbn, "title": title, "author": author, "year": year})

            print(f"Added book with isbn {isbn}.")

    print("Imported Successfully")
    db.commit()


if __name__ == "__main__":
    main()
    
