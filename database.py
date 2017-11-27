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
    CREATE TABLE caspserver(id int, method int REFERENCES method(id), type text, PRIMARY KEY (id, method));
    CREATE TABLE competesin(caspserver int REFERENCES caspserver(id), casp int REFERENCES casp(id), PRIMARY KEY (caspserver, casp));
    CREATE TABLE target(id text, len int, casp int REFERENCES casp(id), path text REFERENCES path(pathway), PRIMARY KEY (id));
    CREATE TABLE domain(id INTEGER PRIMARY KEY ASC, method int REFERENCES method(id));
    CREATE TABLE component(id INTEGER PRIMARY KEY, target text REFERENCES target(id), num int, domain int REFERENCES domain(id));
    CREATE TABLE segment(start int, stop int, len int, domain int REFERENCES domain(id), PRIMARY KEY (start, domain));
    CREATE TABLE model(id INTEGER PRIMARY KEY, method int REFERENCES method(id), target int REFERENCES target(id), path text UNIQUE REFERENCES path(pathway), name text, UNIQUE(method, target, name));
    CREATE TABLE qa(id INTEGER PRIMARY KEY, model int REFERENCES model(id), component int REFERENCES component(id), method int REFERENCES method(id), UNIQUE (model, component, method));
    CREATE TABLE qascore(qa int REFERENCES qa(id) PRIMARY KEY, global real);
    CREATE TABLE lscore(qa int REFERENCES qa(id), residue int, score real, PRIMARY KEY (qa, residue));
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
        "CREATE TABLE caspserver(id int, method int REFERENCES method(id), type text, PRIMARY KEY (id, method));")
    database.execute(
        "CREATE TABLE competesin(caspserver int REFERENCES caspserver(id), casp int REFERENCES casp(id), PRIMARY KEY (caspserver, casp));")
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
        "CREATE TABLE qascore(qa int REFERENCES qa(id) PRIMARY KEY, global real);")
    database.execute(
        "CREATE TABLE lscore(qa int REFERENCES qa(id), residue int, score real, PRIMARY KEY (qa, residue));")
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


def get_caspserver_name(database, server):
    query = 'SELECT name FROM caspserver WHERE id = {};'.format(server)
    result = database.execute(query).fetchone()
    if result is None:
        raise IndexError
    return result[0]


def get_caspserver_method(database, server):
    query = 'SELECT method FROM caspserver WHERE id = {};'.format(server)
    result = database.execute(query).fetchone()
    if result is None:
        raise IndexError
    return result[0]


def get_correlates(database, methods, target=None):
    """ Get QA local scorecorrelates for a target over a set of methods

    :param database: sqlite3 database connection
    :param methods: list with integer method ID's
    :param target: Stirng with target identifier. if specified, only get
                   correlates pertaining to target
    :return: list of tuples with residue number as first element and local
                scores from all QA's found
    """
    # query = "select id, name from method where type = 2 or type = 3;"
    # methods = database.execute(query).fetchall()

    models = get_models(database, target=target)

    qa_query = "SELECT id FROM qa WHERE model = {} AND method = {} AND component IS NULL"
    score_query = "SELECT residue, score FROM lscore WHERE qa = {}"

    correlates = []
    for model in models:
        new_correlates = get_model_correlates(database, model, methods)
        if new_correlates is not None:
            correlates += new_correlates
    return correlates


def get_model_correlates(database, model, methods):
    """ Get correlates for a model, over specified methods

    :param database: sqlite3 connection
    :param model: integer model ID
    :param methods: list of integer method IDs
    :return: list of tuples with float correlates
    """
    qa_query = "SELECT id FROM qa WHERE model = {} AND method = {} AND component IS NULL"
    score_query = "SELECT residue, score FROM lscore WHERE qa = {}"

    selects = []
    froms = []
    ons = []
    previous = None
    skip = False
    # print("MODEL: {}".format(model))
    for (num, method_id) in enumerate(methods):
        tablename = "t{}".format(num)
        qa = database.execute(qa_query.format(model, method_id)).fetchone()
        if qa is not None:
            # print("TABLE NUM: {}, METHOD ID: {}".format(num, method_id))
            qa = qa[0]
            if previous is None:
                selects.append("{}.residue".format(tablename))
            selects.append("{}.score".format(tablename))
            froms.append("({}) AS {}".format(score_query.format(qa), tablename))
            if previous is not None:
                ons.append(
                    "{}.residue = {}.residue".format(previous, tablename))
            previous = tablename
        else:
            # print("SKIPPING")
            skip = True
            break
    if skip:
        return None
    current_query = "SELECT {} FROM {} ON {};".format(", ".join(selects),
                                                      ", ".join(froms),
                                                      " AND ".join(ons))
    # print(current_query)
    return database.execute(current_query).fetchall()


def get_method_id_from_type(database, methodtype):
    """ Get method ID's for all methods of a specified type

    :param database: sqlite3 connection
    :param methodtype: integer of method type
    :return: list of method ID integers
    """
    query = 'SELECT id FROM method WHERE type = {};'.format(methodtype)
    result = database.execute(query).fetchall()
    if result is None:
        raise IndexError
    return [entry[0] for entry in result]

def get_method_type(database, method):
    query = 'SELECT type FROM method WHERE id = {};'.format(method)
    result = database.execute(query).fetchone()
    if result is None:
        raise IndexError
    return result[0]


def get_method_name(database, method):
    query = 'SELECT name FROM method WHERE id = {};'.format(method)
    result = database.execute(query).fetchone()
    if result is None:
        raise IndexError
    return result[0]


def get_method_id_and_name_from_type(database, methodtypes):
    """ Get lists of method id and name of a selection of method types

    :param database: sqlite3 connection
    :param methodtypes: list of string method type names
    :return: tuple of lists with method ID integers and method name strings
    """
    method_ids = []
    for methodtype in methodtypes:
        method_ids += get_method_id_from_type(database, method_type[methodtype])
    method_names = [get_method_name(database, method_id) for method_id in method_ids]
    return method_ids, method_names


def get_models(database, target=None):
    query = "select id from model;"
    # Select only pertaining to a target if specified
    if target is not None:
        query = 'SELECT id FROM model WHERE target = "{}";'.format(target)
    return [entry[0] for entry in database.execute(query).fetchall()]


def get_model_id_from_method_target_name(database, method, target, name):
    query = 'select id from model WHERE method = {} AND target = "{}" AND name = "{:02d}"'.format(method, target, name)
    result = database.execute(query).fetchone()
    if result is None:
        raise IndexError
    return result[0]


def update_caspserver_method(database, server, method):
    query = 'UPDATE caspserver SET method = {} WHERE id = {};'.format(method, server)
    return database.execute(query)


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
    print(query)
    method = database.execute(query).fetchone()

    # Otherwise insert a new method
    if method is None:
        query = 'INSERT INTO method (name, description, type) VALUES ("{}", "{}", {})'.format(
            method_name, method_desc, method_type[method_type_name])
        database.execute(query)
        method = database.execute("SELECT last_insert_rowid();").fetchone()

    return method[0]

    # select t1.model, t1.score, t2.score from
    # (select qa.model as model, qascore.global as score from qa inner join qascore on qa.id = qascore.qa where qa.method = 51) as t1,
    # (select qa.model as model, qascore.global as score from qa inner join qascore on qa.id = qascore.qa where qa.method = 52) as t2
    # on t1.model = t2.model;
def query_global_correlates(methods):
    """Format query for global correlates over QA model intersection

    :param methods: iterable of model integer ID's to intersect
    :return: string of sqlite3 query
    """
    from_query = "SELECT qa.model AS model, qascore.global AS score FROM qa INNER JOIN qascore ON qa.id = qascore.qa WHERE qa.method = {} AND qa.component IS NULL"

    selects = []
    froms = []
    ons = []
    previous = None

    for (num, method_id) in enumerate(methods):
        tablename = "t{}".format(num)
        froms.append("({}) AS {}".format(from_query.format(method_id), tablename))
        # Report model as first column
        if previous is not None:
            ons.append(
                    "{}.model = {}.model".format(previous, tablename))
        else:
            selects.append("{}.model".format(tablename))
        selects.append("{}.score".format(tablename))
        previous = tablename

    return "SELECT {} FROM {} ON {};".format(", ".join(selects),
                                             ", ".join(froms),
                                             " AND ".join(ons))


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
    query = 'SELECT id FROM qa WHERE model = {} AND component {} AND method = {};'.format(model, "IS NULL" if component is None else "= {}".format(component), qa_method)
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
    query = 'INSERT OR REPLACE INTO qascore (qa, global) VALUES ({}, {:.3f})'.format(qa_id, global_score)
    database.execute(query)
    store_local_score(qa_id, local_score, database)
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

    # Remove all known old QAjoins from the join table
    query = 'DELETE FROM qajoin WHERE compound = {};'.format(qa_cmp_id)
    database.execute(query)

    # for every entry in qas, generate a QAjoin entry
    for qa in qas:
        query = 'INSERT INTO qajoin (qa, compound) VALUES ({}, {})'.format(qa, qa_cmp_id)
        # If query fails, do nothing, all is good
        # try:
        #     database.execute(query)
        # except IntegrityError:
        #     pass
        database.execute(query)
    return qa_cmp_id


def store_local_score(qa, local_score, database):
    """Store a list of local scores in database

    :param qa: integer id of the quality assessment that the score pertains to
    :param local_score: list of floats with local scores, always starting with
                        score of first residue, even if not part of model scored
    :param database: database connection
    """
    # Create the table
    query = "CREATE TABLE IF NOT EXISTS lscore(qa int REFERENCES qa(id), residue int, score real, PRIMARY KEY (qa, residue));"
    database.execute(query)

    # Store the data
    query = 'INSERT OR REPLACE INTO lscore (qa, residue, score) VALUES (?, ?, ?)'
    # Expect local score to always start from 1st residue
    for (residue, score) in enumerate(local_score, start=1):
        # only store the existing assessments
        if score is not None:
            database.execute(query, (qa, residue, score))


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


def store_caspservers(servers, casp, database, all=False):
    """Save parsed casp-servers in database, if method already present

    :param servers: Dictionary with integer server CASP id as keys and tuples of
                    server name string and type string as values
    :param casp: integer with casp experiment ID
    :param database: sqlite3 database connection
    :return: dictionary with all added CASP server id integers as keys and
             server name as values
    """
    database.execute(
        "CREATE TABLE IF NOT EXISTS caspserver(id int, method int REFERENCES method(id), name text, type text, PRIMARY KEY (id, method));")
    database.execute(
        "CREATE TABLE IF NOT EXISTS competesin(caspserver int REFERENCES caspserver(id), casp int REFERENCES casp(id), PRIMARY KEY (caspserver, casp));")

    added = {}
    for server in servers:
        query = 'SELECT id FROM method WHERE name = ?;'
        servername = servers[server][0]
        servertype = servers[server][1]
        method = database.execute(query, (servername,)).fetchone()
        if method is not None:
            method = method[0]
        if all or method is not None:
            query = 'INSERT OR REPLACE INTO caspserver (id, method, name, type) VALUES (?, ?, ?, ?);'
            database.execute(query, (server, method, servername, servertype))
            query = 'INSERT OR REPLACE INTO competesin (caspserver, casp) VALUES (?, ?)'
            database.execute(query, (server, casp))
            added[server] = servers[server][0]

    return added


def store_domains(domains, database, method, casp=12):
    # Check if CASP is present, or create it
    if database.execute(
            "SELECT EXISTS (SELECT * FROM casp WHERE id = {} LIMIT 1);".format(
                casp)).fetchone()[0] == 0:
        database.execute("INSERT INTO casp (id) VALUES ({});".format(casp))
    # Create new method if not specified
    if method is None:
        database.execute('INSERT INTO method (name, description, type) VALUES ("{}", "{}", {});'.format("Unkonwn Partitioner", "Automatically inserted unknown partition method", method_type["partitioner"]))
        method = database.execute("SELECT last_insert_rowid();").fetchone()[0]
    # Or insert new if specified but does not exist
    elif database.execute(
            "SELECT EXISTS (SELECT * FROM method WHERE id = {} LIMIT 1);".format(
                method)).fetchone()[0] == 0:
        database.execute('INSERT INTO method (id, name, description, type) VALUES ({}, "{}", "{}", {});'.format(method, "Unkonwn Partitioner", "Automatically inserted unknown partition method", method_type["partitioner"]))
    for target in domains:
        # check if target is present, or create it
        if database.execute(
                'SELECT EXISTS (SELECT * FROM target WHERE id = "{}" LIMIT 1);'.format(
                 target)).fetchone()[0] == 0:
            database.execute(
                'INSERT INTO target (id, casp) VALUES ("{}", {});'.format(target, casp))
        for (num, domain) in enumerate(domains[target]):
            # check if domain is present, or create it
            domain_id = database.execute(
                'SELECT domain.id FROM component INNER JOIN domain ON (component.domain = domain.id) WHERE component.target = "{}" AND component.num = {} AND domain.method = {} LIMIT 1;'.format(
                    target, num, method)).fetchone()
            print(domain_id)
            if domain_id is None:
                # Insert new domain
                database.execute(
                    'INSERT INTO domain (method) VALUES ({});'.format(method))
                # Get last inserted domains rowid (domain id)
                domain_id = database.execute("SELECT last_insert_rowid();").fetchone()
                # Create component connector
                database.execute(
                    'INSERT INTO component (target, num, domain) VALUES ("{}", {}, {});'.format(
                        target, num, domain_id[0]))
                print("Inserted domain {}".format(domain_id[0]))
            domain_id = domain_id[0]
            print("And again {}".format(domain_id))
            for segment in domain:
                # print(segment, type(segment))
                database.execute('INSERT INTO segment (domain, start, stop) VALUES ({}, {}, {});'.format(domain_id, segment[0], segment[1]))


def store_or_get_model(target, method, model, database):
    """ Store a new model or find model id for already stored model

    :param target: text of CASP target ID
    :param method: integer method ID
    :param model: integer model serial, i.e. server submission serial
    :param database: database connection
    :return: integer stored model ID
    """
    query = 'INSERT INTO model (method, target, name) VALUES ({}, "{}", "{:02d}")'.format(
        method, target, model)
    try:
        database.execute(query)
        model_id = database.execute("SELECT last_insert_rowid();").fetchone()[0]
    except IntegrityError:
        query = 'SELECT id FROM model WHERE method = {} AND target = "{}" AND name = "{:02d}"'.format(
            method, target, model)
        model_id = database.execute(query).fetchone()[0]
    return model_id


def store_model_caspmethod(target, caspserver, model, database):
    """Store model, using CASP server ID's

    :param target: text of CASP target ID
    :param caspserver: integer CASP server ID
    :param model: integer server model serial
    :param database: database connection
    :return: integer model ID stored or found in database
    """
    try:
        # Get method of caspserver
        query = "SELECT method FROM caspserver WHERE id = {};".format(caspserver)
        method_id = database.execute(query).fetchone()[0]
        # Get model ID if present
        model_id = store_or_get_model(target, method_id, model, database)
    except TypeError:
        return None

    return model_id


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
        # Find, or store new models
        for model in servers[server]:
            model_id[(server, model)] = store_or_get_model(target, servermethod,
                                                           model, database)
            # # CREATE TABLE model(id INTEGER PRIMARY KEY, method int REFERENCES method(id), target int REFERENCES target(id), path text REFERENCES path(pathway), name text);
            # query = 'INSERT INTO model (method, target, name) VALUES ({}, "{}", "{:02d}")'.format(servermethod, target, model)
            # try:
            #     database.execute(query)
            #     model_id[(server, model)] = \
            #     database.execute("SELECT last_insert_rowid();").fetchone()[0]
            # except IntegrityError:
            #     query = 'SELECT id FROM model WHERE method = {} AND target = "{}" AND name = "{:02d}"'.format(servermethod, target, model)
            #     model_id[(server, model)] = database.execute(query).fetchone()[0]
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


def store_target_information(targets, casp, database, target_key="Target", length_key="Res", force=False):
    """Store CASP target specifications in database

    :param targets: csv.DictionaryReader with CASP target specifications
    :param casp: integer CASP id
    :param database: sqlite3 database connection
    :param target_key: string text column identifier for target keys (specified
                       in first line of csv)
    :param length_key: dito but for the number of residues in target
    :param force: Store new targets if not already present in database, default
                  is to only update targets already found in database
    :return: tuple with two dictionaries
             1) all found target text identifiers as keys, found text string of
                target length as values
             2) all saved targets, text identifiers as keys and tuples of target
                integer length, integer casp ID and text path (if present) as
                values
    """

    found = {}
    saved = {}
    # Parse each entry found
    for entry in targets:
        target = entry[target_key]
        length = entry[length_key]
        # Check if entry is stored
        query = 'SELECT id, len, casp, path FROM target WHERE id = "{}";'.format(target)
        stored = database.execute(query).fetchone()
        found[target] = length
        # Save new length if found
        if stored is not None:
            length = int(length)
            (stored_id, stored_len, stored_casp, stored_path) = stored
            query = 'INSERT OR REPLACE INTO target (id, len, casp, path) VALUES (?, ?, ?, ?);'
            database.execute(query, (target, length, casp, stored_path))
            saved[target] = (length, casp, stored_path)
        # Otherwise create new entry with indicated length, if forcing adding
        elif force:
            length = int(length)
            query = 'INSERT INTO target (id, len, casp) VALUES (?, ?, ?);'
            database.execute(query, (target, length, casp))
            saved[target] = (length, casp, None)

    return (found, saved)


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