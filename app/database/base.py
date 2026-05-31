from sqlalchemy.orm import declarative_base

# This is the base class that all our database models will inherit from.
# It acts as a catalog of all the tables and columns we define.
Base = declarative_base()
