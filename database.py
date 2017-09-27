from sqlite3 import connect, IntegrityError
from .interface.pcons import write_local_scores
from .interface.targets import identify_models_and_servers
from .definitions import method_type


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
    CREATE TABLE model(id INTEGER PRIMARY KEY, method int REFERENCES method(id), target int REFERENCES target(id), path text UNIQUE REFERENCES path(pathway), name text, UNIQUE(method, target, name));
    CREATE TABLE qa(id INTEGER PRIMARY KEY, model int REFERENCES model(id), component int REFERENCES component(id), method int REFERENCES method(id), UNIQUE (model, component, method));
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
        "CREATE TABLE model(id INTEGER PRIMARY KEY, method int REFERENCES method(id), target int REFERENCES target(id), path text UNIQUE REFERENCES path(pathway), name text, UNIQUE(method, target, name));")
        #"CREATE TABLE model(id INTEGER PRIMARY KEY, method int REFERENCES method(id), target int REFERENCES target(id), path text REFERENCES path(pathway), name text);")
    database.execute(
        "CREATE TABLE qa(id INTEGER PRIMARY KEY, model int REFERENCES model(id), component int REFERENCES component(id), method int REFERENCES method(id), UNIQUE (model, component, method));")
        #"CREATE TABLE qa(id INTEGER PRIMARY KEY, model int UNIQUE REFERENCES model(id), component int UNIQUE REFERENCES component(id), method int UNIQUE REFERENCES method(id));")
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

    # check if there is already a unique qa entry
    query = 'SELECT id FROM qa WHERE model = {} AND component {} AND method = {};'.format(model, "IS NULL" if component is None else "= " + component, qa_method)
    qa_id = database.execute(query).fetchone()
    print(query)
    print(qa_id)
    if qa_id is None:
        query = 'INSERT INTO qa (model, component, method) VALUES ({}, {}, {})'.format(model, "NULL" if component is None else component, qa_method)
        database.execute(query)
        # Get auto-generated quality assessment ID
        qa_id = database.execute("SELECT last_insert_rowid();").fetchone()
    qa_id = qa_id[0]
    # Insert new or overwrite qascore entry
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
    qa_cmp_id = store_qa(model, global_score, local_score, cmp_method, database)

    # query = 'INSERT INTO qa (model, component, method) VALUES ({}, {}, {})'.format(model, "NULL", cmp_method)
    # database.execute(query)
    # qa_cmp_id = database.execute("SELECT last_insert_rowid();").fetchone()
    # # Store score
    # query = 'INSERT INTO qascore (qa, global, local) VALUES ({}, {:.3f}, "{}")'.format(qa_cmp_id, global_score, write_local_scores(local_score))
    # database.execute(query)

    # for every entry in qas, generate a QAjoin entry
    for qa in qas:
        query = 'INSERT INTO qajoin (qa, compound) VALUES ({}, {})'.format(qa, qa_cmp_id)
        database.execute(query)
    return qa_cmp_id


def store_servers(servers, database):
    """Store or fetch server methods in/from database

    :param servers: iterable yielding server names
    :param database: database connection
    :return: dictionary with server names as keys and integer method ID's as
             values
    """
    server_methods = {}
    for server in servers:
        server_methods[server] = get_or_add_method(server, "", "server",
                                                   database)
    return server_methods


def store_models(target, servers, servermethods, database):
    """Store models in database

    :param target: integer target ID that models pertain to
    :param models: dictionary with server names as keys and lists of model
                   numbers as values
    :param servermethods: dictionary with server names as keys and integer
                          server method ID's as values
    :param database: database connection
    :return: dictionary with tuples of server name and model number as keys and
             integer model ID as values
    """

    model_id = {}
    for server in servers:
        # identify servermethod ID
        servermethod = servermethods[server]
        for model in servers[server]:
            # CREATE TABLE model(id INTEGER PRIMARY KEY, method int REFERENCES method(id), target int REFERENCES target(id), path text REFERENCES path(pathway), name text);
            query = 'INSERT INTO model (method, target, name) VALUES ({}, "{}", "{:02d}")'.format(servermethod, target, model)
            try:
                database.execute(query)
                model_id[(server, model)] = \
                database.execute("SELECT last_insert_rowid();").fetchone()[0]
            except IntegrityError:
                query = 'SELECT id FROM model WHERE method = {} AND target = "{}" AND name = "{:02d}"'.format(servermethod, target, model)
                model_id[(server, model)] = database.execute(query).fetchone()[0]
    return model_id


def store_models_and_servers(target, results, database):
    """Stores new servers and models; wrapper for store_servers and store_models

    :param target: text target ID that models pertain to
    :param results: pcons results tuple as parsed by this library, see
                    identify_models_and_servers
    :param database: database connection
    :return: returns all returnables generated by, and in order
             1) identify_models_and_servers
             2) store_servers
             3) store_models
    """
    (servers, modeltuples, filenames) = identify_models_and_servers(results[0])
    servermethods = store_servers(servers, database)
    model_id = store_models(target, servers, servermethods, database)

    return servers, modeltuples, filenames, servermethods, model_id


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


def save_or_dump(database, datafile):
    """Commit and close database, or dump to STDOUT

    :param database: database connection
    :param datafile: string with database filename, if None; blurt out to STDOUT
    """
    if datafile is not None:
        database.commit()
        database.close()
    else:
        # or blurt sql-dump to stdout, if no database specified
        for line in database.iterdump():
            print(line)