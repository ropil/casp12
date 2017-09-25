from sqlite3 import connect


method_type = {"server" : 0, "partitioner" : 1, "qa" : 2, "compounder" : 3 }


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


def create_result_database(db=":memory:"):
    # Create in-memory
    """Creates the database, in memory, to use for analyzing domain partitions

    :return: the database connection handle
    """

    '''Copy the following to sqlite3 prompt to try it in console
    CREATE TABLE path(pathway text PRIMARY KEY);
    CREATE TABLE casp(id int PRIMARY KEY, path REFERENCES path(pathway));
    CREATE TABLE method(id INTEGER PRIMARY KEY ASC, name text, description text, type int);
    CREATE TABLE target(id text, len int, casp int REFERENCES casp(id), path text REFERENCES path(pathway), PRIMARY KEY (id));
    CREATE TABLE domain(id INTEGER PRIMARY KEY ASC, method int REFERENCES method(id));
    CREATE TABLE component(target text REFERENCES target(id), num int, domain int REFERENCES domain(id), PRIMARY KEY (target, num, domain));
    CREATE TABLE segment(start int, stop int, len int, domain int REFERENCES domain(id), PRIMARY KEY (start, domain));
    CREATE TABLE model(id int PRIMARY KEY, method int REFERENCES method(id), target int REFERENCES target(id), path text REFERENCES path(pathway), name text);
    CREATE TABLE qa(id int PRIMARY KEY, model int REFERENCES model(id), domain int REFERENCES domain(id), method int REFERENCES method(id));
    CREATE TABLE qascore(model int REFERENCES model(id), domain int REFERENCES domain(id), method int REFERENCES method(id), global int, local text, PRIMARY KEY (model, domain, method));
    CREATE TABLE qacompound(id int PRIMARY KEY, method int REFERENCES method(id), model int REFERENCES model(id));
    CREATE TABLE qajoin(qa int REFERENCES qa(id), compound int REFERENCES qacompound(id), PRIMARY KEY (qa, compound));
    # Segment triggers;
    CREATE TRIGGER segment_length_insert AFTER INSERT ON segment FOR EACH ROW BEGIN UPDATE segment SET len = NEW.stop - NEW.start + 1 WHERE domain = NEW.domain AND start = NEW.start AND stop = NEW.stop; END;
    CREATE TRIGGER segment_length_update AFTER UPDATE ON segment FOR EACH ROW BEGIN UPDATE segment SET len = NEW.stop - NEW.start + 1 WHERE domain = NEW.domain AND start = NEW.start AND stop = NEW.stop; END;
    # Domain size view, sorted by largest domain;
    CREATE VIEW domain_size (target, method, domain, id, dlen, nseg) AS SELECT component.target, domain.method, component.num, domain.id, SUM(segment.len), COUNT(*) FROM domain INNER JOIN segment ON (domain.id = segment.domain) INNER JOIN component on (component.domain = domain.id) GROUP BY domain.id;
    '''

    database = connect(db)

    database.execute("CREATE TABLE path(pathway text PRIMARY KEY);")
    database.execute(
        "CREATE TABLE casp(id int PRIMARY KEY, path REFERENCES path(pathway));")
    database.execute(
        "CREATE TABLE method(id INTEGER PRIMARY KEY ASC, name text, description text, type int);")
    database.execute(
        "CREATE TABLE target(id text, len int, casp int REFERENCES casp(id), path text REFERENCES path(pathway), PRIMARY KEY (id));")
    database.execute(
        "CREATE TABLE domain(id INTEGER PRIMARY KEY ASC, method int REFERENCES method(id));")
    database.execute(
        "CREATE TABLE component(target text REFERENCES target(id), num int, domain int REFERENCES domain(id), PRIMARY KEY (target, num, domain));")
    database.execute(
        "CREATE TABLE segment(start int, stop int, len int, domain int REFERENCES domain(id), PRIMARY KEY (start, domain));")
    database.execute(
        "CREATE TABLE model(id int PRIMARY KEY, method int REFERENCES method(id), target int REFERENCES target(id), path text REFERENCES path(pathway), name text);")
    database.execute(
        "CREATE TABLE qa(id int PRIMARY KEY, model int REFERENCES model(id), domain int REFERENCES domain(id), method int REFERENCES method(id));")
    database.execute(
        "CREATE TABLE qascore(model int REFERENCES model(id), domain int REFERENCES domain(id), method int REFERENCES method(id), global int, local text, PRIMARY KEY (model, domain, method));")
    database.execute(
        "CREATE TABLE qacompound(id int PRIMARY KEY, method int REFERENCES method(id), model int REFERENCES model(id));")
    database.execute(
        "CREATE TABLE qajoin(qa int REFERENCES qa(id), compound int REFERENCES qacompound(id), PRIMARY KEY (qa, compound));")
    # Segment triggers;
    database.execute(
        "CREATE TRIGGER segment_length_insert AFTER INSERT ON segment FOR EACH ROW BEGIN UPDATE segment SET len = NEW.stop - NEW.start + 1 WHERE domain = NEW.domain AND start = NEW.start AND stop = NEW.stop; END;")
    database.execute(
        "CREATE TRIGGER segment_length_update AFTER UPDATE ON segment FOR EACH ROW BEGIN UPDATE segment SET len = NEW.stop - NEW.start + 1 WHERE domain = NEW.domain AND start = NEW.start AND stop = NEW.stop; END;")
    # Domain size view, sorted by largest domain;
    database.execute(
        "CREATE VIEW domain_size (target, method, domain, id, dlen, nseg) AS SELECT component.target, domain.method, component.num, domain.id, SUM(segment.len), COUNT(*) FROM domain INNER JOIN segment ON (domain.id = segment.domain) INNER JOIN component on (component.domain = domain.id) GROUP BY domain.id;")

    return database