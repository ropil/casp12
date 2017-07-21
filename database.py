from sqlite3 import connect


def create_database(db=":memory:"):
    # Create in-memory
    """Creates the database, in memory, to use for analyzing domain partitions

    :return: the database connection handle
    """

    '''Copy the following to sqlite3 prompt to try it in console
    CREATE TABLE casp(id int PRIMARY KEY);
    CREATE TABLE target(id text, len int, casp int REFERENCES casp(id), PRIMARY KEY (id, casp));
    CREATE TABLE domain(num int, target text REFERENCES target(id), casp int REFERENCES target(casp), PRIMARY KEY (num, target, casp));
    CREATE TABLE segment(start int, stop int, len int, domain int REFERENCES domain(num), target text REFERENCES domain(target), casp int REFERENCES domain(casp), PRIMARY KEY (start, domain, target, casp));
    CREATE TRIGGER segment_length_insert BEFORE INSERT ON segment FOR EACH ROW BEGIN UPDATE NEW SET len = stop - start + 1; END;
    CREATE TRIGGER segment_length_update BEFORE UPDATE ON segment FOR EACH ROW BEGIN UPDATE NEW SET len = stop - start + 1; END;
    CREATE VIEW domain_size (casp, target, domain, dlen, nseg) AS SELECT domain.casp, domain.target, domain.num, SUM(segment.len), COUNT(*) FROM domain INNER JOIN segment ON (domain.casp = segment.casp AND domain.target = segment.target AND domain.num = segment.domain) GROUP BY domain.casp, domain.target, domain.num;
    '''

    database = connect(db)
    # CASP table
    database.execute("CREATE TABLE casp(id int PRIMARY KEY);")
    # CASP targets table
    #
    database.execute("CREATE TABLE target(id text, " +
                     "len int, " +
                     "casp int REFERENCES casp(id), " +
                     "PRIMARY KEY (id, casp));")
    # Corresponding domains table
    # "CREATE TABLE domain(num int, target text REFERENCES target(id), casp int REFERENCES target(casp), PRIMARY KEY (num, target, casp));
    database.execute("CREATE TABLE domain(num int, " +
                     "target text REFERENCES target(id), " +
                     "casp int REFERENCES target(casp), " +
                     "PRIMARY KEY (num, target, casp));")
    # Segment definitions table
    database.execute(
        "CREATE TABLE segment(start int, stop int, len int, domain int REFERENCES domain(num), target text REFERENCES domain(target), casp int REFERENCES domain(casp), PRIMARY KEY (start, domain, target, casp));")
    # Synthetic variables
    # Triggers for segment length calculation
    database.execute(
        "CREATE TRIGGER segment_length_insert AFTER INSERT ON segment FOR EACH ROW BEGIN UPDATE segment SET len = NEW.stop - NEW.start + 1 WHERE casp = NEW.casp AND target = NEW.target AND domain = NEW.domain AND start = NEW.start AND stop = NEW.stop; END;")
    database.execute(
        "CREATE TRIGGER segment_length_update AFTER UPDATE ON segment FOR EACH ROW BEGIN UPDATE segment SET len = NEW.stop - NEW.start + 1 WHERE casp = NEW.casp AND target = NEW.target AND domain = NEW.domain AND start = NEW.start AND stop = NEW.stop; END;")
    # Domain size view, sorted by largest domain
    database.execute(
        "CREATE VIEW domain_size (casp, target, domain, dlen, nseg) AS SELECT domain.casp, domain.target, domain.num, SUM(segment.len), COUNT(*) FROM domain INNER JOIN segment ON (domain.casp = segment.casp AND domain.target = segment.target AND domain.num = segment.domain) GROUP BY domain.casp, domain.target, domain.num;")
    return database