from sqlite3 import connect
from casp12.interface.pcons import write_local_scores


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
    CREATE TABLE component(id INTEGER PRIMARY KEY, target text REFERENCES target(id), num int, domain int REFERENCES domain(id));
    CREATE TABLE segment(start int, stop int, len int, domain int REFERENCES domain(id), PRIMARY KEY (start, domain));
    CREATE TABLE model(id int PRIMARY KEY, method int REFERENCES method(id), target int REFERENCES target(id), path text REFERENCES path(pathway), name text);
    CREATE TABLE qa(id INTEGER PRIMARY KEY, model int REFERENCES model(id), component int REFERENCES component(id), method int REFERENCES method(id));
    CREATE TABLE qascore(qa int REFERENCES qa(id) PRIMARY KEY, global float, local text);
    CREATE TABLE qajoin(qa int REFERENCES qa(id), compound int REFERENCES qa(id), PRIMARY KEY (qa, compound));
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
        "CREATE TABLE component(id INTEGER PRIMARY KEY, target text REFERENCES target(id), num int, domain int REFERENCES domain(id))")
    database.execute(
        "CREATE TABLE segment(start int, stop int, len int, domain int REFERENCES domain(id), PRIMARY KEY (start, domain));")
    database.execute(
        "CREATE TABLE model(id int PRIMARY KEY, method int REFERENCES method(id), target int REFERENCES target(id), path text REFERENCES path(pathway), name text);")
    database.execute(
        "CREATE TABLE qa(id INTEGER PRIMARY KEY, model int REFERENCES model(id), component int REFERENCES component(id), method int REFERENCES method(id));")
    database.execute(
        "CREATE TABLE qascore(qa int REFERENCES qa(id) PRIMARY KEY, global float, local text);")
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


def store_qa(model, global_score, local_score, qa_method, database, component=None):
    """Store quality assessment scores, either full model or partitioned domain

    :param model: integer, server model ID
    :param global_score: float of global quality score
    :param local_score: vector of floats containing local score
    :param qa_method: integer id of quality assessment method
    :param database: sqlite3 database connection
    :param component: integer of component ID; None for full unpartitioned
                      method
    :return: id of QA entry created
    """
    query = 'INSERT INTO qa (model, component, method) VALUES ({}, {}, {})'.format(model, component, qa_method)
    database.execute(query)
    # Get auto-generated quality assessment ID
    qa_id = database.execute("SELECT last_insert_rowid();").fetchone()
    query = 'INSERT INTO qascore (qa, global, local) VALUES ({}, {:.3f}, "{}")'.format(qa_id, global_score, write_local_scores(local_score))
    database.execute(query)
    return qa_id


def store_qa_compounded(model, qas,  global_score, local_score, cmp_method, database):
    """Store quality assessment scores for a compounded quality

    :param model: integer id of model score pertains to
    :param qas: list of integer id's for quality assessments used in compounding
    :param global_score: float of global compounded quality
    :param local_score: list of floats with local compounded quality
    :param cmp_method: integer id of compounding method
    :param database: database connection
    :return: integer id of QA entry created
    """
    # Store compounded entry
    query = 'INSERT INTO qa (model, component, method) VALUES ({}, {}, {})'.format(model, None, cmp_method)
    database.execute(query)
    qa_cmp_id = database.execute("SELECT last_insert_rowid();").fetchone()
    # Store score
    query = 'INSERT INTO qascore (qa, global, local) VALUES ({}, {:.3f}, "{}")'.format(qa_cmp_id, global_score, write_local_scores(local_score))
    database.execute(query)
    # for every entry in qas, generate a QAjoin entry
    for qa in qas:
        query = 'INSERT INTO qascore (qa, compound) VALUES ({}, {})'.format(qa, qa_cmp_id)
        database.execute(query)
    return qa_cmp_id


def get_or_add_method(method_name, method_desc, method_type_name, database):
    """Get or add a method following its name, description and type definition

    :param method_name: str with name of method
    :param method_desc: str with method description
    :param method_type_name: str of method type name, see method_type dictionary
    :param database: database connection
    :return: integer method id
    """
    # Try to find the method id, if it exists

    query = 'SELECT id FROM method WHERE name = "{}" AND description = "{}" AND type = {} LIMIT 1'.format(
        method_name, method_desc, method_type[method_type_name])
    method = database.execute(query).fetchone()

    # Otherwise insert a new method
    if method is None:
        query = 'INSERT INTO method (name, description, type) VALUES ("{}", "{}", {})'.format(
            method_name, method_desc, method_type[method_type_name])
        database.execute(query)
        method = database.execute("SELECT last_insert_rowid();").fetchone()

    return method[0]