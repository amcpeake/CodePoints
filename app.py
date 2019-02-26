def pyde(req, mem=64, time=30):  # Take input parameters, pass them to PyDE and get the results
    if mem > 64 or not isinstance(mem, int):  # Max memory in MB
        mem = 64

    if time > 30 or not isinstance(time, int):  # Max time in seconds
        time = 30

    req['timeout'] = time

    numconts = subprocess.run(['docker ps | grep \'pyde\' | wc -l'], stdout=subprocess.PIPE, shell=True)
    if int(numconts.stdout.decode('utf-8')) > 5:  # Determine number of active docker containers
        return dict({'status': 'fail', 'error': ['Resource Utilization Error: Too many active containers']})

    else:
        try:
            resp = subprocess.run(['docker', 'run',
                                   f'--memory={mem}m',
                                   f'--memory-swap={mem}m',
                                   f'--kernel-memory={mem}m',
                                   '--cpus=0.2',
                                   '--cpu-shares=32',
                                   '--cpuset-cpus=3',
                                   '--network', 'none',
                                   '--pids-limit=32',
                                   '--rm',
                                   'pyde', f'{json.dumps(req)}'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  timeout=time)

        except subprocess.TimeoutExpired:
            return dict({'status': 'fail', 'error': ['Program timed out']})

        else:
            try:
                return json.loads(resp.stdout.decode('utf-8'))

            except json.decoder.JSONDecodeError:
                return dict({'status': 'fail', 'error': 'JSON Parsing Error: Malformed JSON Received from handler'})


# ======================================================================================================================


def getrandom(inp, out):  # Convert input min/max values to a random integer and get corresponding output
    inputcase = []
    outputcase = []
    for var in inp:
        if var['type'] == 'int':
            minimum = int(var['min'])
            maximum = int(var['max'])
        if var['type'] == 'char':
            minimum = ord(var['min'])
            maximum = ord(var['max'])
        inputcase.append(random.choice(list(range(minimum, maximum + 1))))

    for var in out:
        outputcase.append(eval(var))

    return inputcase, outputcase


# ======================================================================================================================


def challengelist(lang, challenges):  # Take in a language and return a list of available challenge indices
    clist = []  # Initialize list of challenges

    for index, challenge in challenges.items():  # Iterate through challenges
        if 'languages' in challenge and (lang in challenge['languages'] or 'any' in challenge['languages']):
            clist.append({'name': challenge['name'], 'index': index})

    return clist  # Return challenge list


# ======================================================================================================================


@app.route('/codepoints', methods=['GET', 'POST'])
def codepoints():
    if request.method == 'POST':  # Used to differentiate between the user loading the web page and sending a request
        # Valid input definitions
        valid = {
            'type': ['list', 'get', 'submit'],
            'language': ['x86', 'bash', 'c', 'cpp', 'c#', 'java', 'javascript', 'php', 'python2', 'python3', 'ruby']
        }

        try:  # Check if request contains a type (i.e. action)
            rtype = request.json['type']
            if rtype not in valid['type']:
                raise KeyError
        except KeyError:  # If not, return an error
            return jsonify({'type': 'error', 'msg': 'Must provide valid request type', 'valid': valid['type']})
        else:  # If so, create a response of the same type
            response = {'type': rtype}

        try:  # Check if request contains a programming language
            language = request.json['language']
            if language not in valid['language']:
                raise KeyError
        except KeyError:  # If not, return an error
            return jsonify({'type': 'error', 'msg': 'Must provide valid language', 'valid': valid['language']})
        else:
            with open(CHALLENGE_FILE) as f:  # Parse challenges file into JSON
                challenges = json.load(f)
            valid['challenges'] = challengelist(language, challenges)

        if rtype == 'list':  # Return a list of available challenges, given the users selected language
            response['challenges'] = valid['challenges']

        else:  # Everything else requires an index
            try:
                index = request.json['index']
                if index not in challenges:
                    raise KeyError
            except KeyError:  # Challenge not given
                return jsonify({'type': 'error',
                                'msg': 'Must provide valid challenge index',
                                'valid': (c.index for c in valid['challenges'])
                                })

        if rtype == 'get':  # Return challenge details
            challenge = challenges[index]
            response['challenge'] = {
                'name': challenge['name'],
                'index': index,
                'description': challenge['description'],
            }

            try:
                challenge['codebase'][language]
            except KeyError:
                pass
            else:
                response['challenge']['codebase'] = challenge['codebase'][language]

            try:
                challenge['io']
            except KeyError:
                pass
            else:
                response['challenge']['io'] = {}
                for i in challenge['io']:
                    response['challenge']['io'][i] = [challenge['io'][i][0]]

        elif rtype == 'submit':  # Take code and compile it
            hrequest = {'language': language}  # Start building the handler request
            challenge = challenges[index]

            try:
                hrequest['code'] = request.json['code']
            except KeyError:
                return jsonify({'type': 'error', 'msg': 'Must provide code to compile'})

            try:
                hrequest['input'] = challenge['io']['input']
            except KeyError:  # Input is not necessary to run code
                pass

            try:
                output = challenge['io']['output']
            except KeyError:
                output = None

            if 'input' in challenge['io'] and 'output' in challenge['io']:
                for cindex, value in enumerate(challenge['io']['input']):
                    if any(isinstance(x, dict) for x in challenge['io']['input'][cindex]):
                        hrequest['input'][cindex], output[cindex] = getrandom(challenge['io']['input'][cindex], 
                                                                              challenge['io']['output'][cindex]
                                                                              )

            hresponse = pyde(hrequest)

            try:
                hstatus = hresponse['status']
            except KeyError:
                return jsonify({'type': 'error', 'msg': 'Malformed response received from handler'})

            if hstatus == 'fail':
                response['status'] = 'fail'
                if 'error' in hresponse:
                    response['errors'] = hresponse['error']

            elif hstatus == 'pass':
                if output:
                    if 'output' in hresponse:
                        response['cases'] = []
                        response['status'] = 'pass'
                        for cidx, case in enumerate(output):
                            cresult = {}
                            if all(str(o).lower() in map(str.lower, hresponse['output'][cidx]) for o in case):
                                cresult['status'] = 'pass'
                            else:
                                cresult['status'] = 'fail'
                                response['status'] = 'fail'
                            if cidx == 0:
                                cresult['values'] = []
                                for oidx, o in enumerate(case):
                                    cresult['values'].append({'expected': str(o), 'actual': '', 'status': ''})
                                    try:
                                        cresult['values'][oidx]['actual'] = str(hresponse['output'][cidx][oidx])
                                    except IndexError:
                                        pass
                                    if str(o).lower() == str(cresult['values'][oidx]['actual']).lower():

                                        cresult['values'][oidx]['status'] = 'pass'
                                    else:
                                        cresult['values'][oidx]['status'] = 'fail'
                            response['cases'].append(cresult)
                    else:
                        response['status'] = 'fail'
                        response['errors'] = ['No output received from code when output was expected']

        return jsonify(response)
    if request.method == 'GET':
        return render_template('codepoints.html')


# ======================================================================================================================


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='80')
