#!/bin/python
import requests, sys, json, signal, logging as log, sched, time, os


# REPLACE THIS SECTION WITH YOUR DNS HANDLER
class DNSHandler():
    def __init__(self, logger:log.Logger, api_key:str = '') -> None:
        self.endpoint = 'https://api.vultr.com/v2'
        self.l = logger
        self.headers = {'Authorization': 'Bearer %s' % api_key}

    def _listRecords(self, site:str) -> list:
        try:
            r = requests.get('%s/domains/%s/records' % (self.endpoint, site), headers=self.headers)
            r.raise_for_status()
            return r.json()['records']
        except Exception as e:
            self.l.error("Failed to list records: %s" % e)
            return []
        
    def _updateRecord(self, site:str, record_id:str, ip:str) -> bool:
        try:
            r = requests.patch('%s/domains/%s/records/%s' % (self.endpoint, site, record_id), headers=self.headers | {'Content-Type':'application/json'}, json={'data': ip})
            r.raise_for_status()
            return True
        except Exception as e:
            self.l.error("Failed to update record: %s" % e)
            return False
# REPLACE THE ABOVE SECTION WITH YOUR DNS HANDLER

class DnsUpdater:
    def __init__(self):
        self.ip = ""
        self.last_ip = ""
        
        self.s = sched.scheduler(time.time, time.sleep)
        
        self.l = log.getLogger('dns-updater')
        self._loadConfig()
        self._setupLogger()
        
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self.handler = DNSHandler(self.l, self.config['api_key'])

    def _interpretLogLevel(self, logstr):
        if logstr == "debug":
            return log.DEBUG
        elif logstr == "info":
            return log.INFO
        elif logstr == "warning" or logstr == "warn":
            return log.WARNING
        elif logstr == "error":
            return log.ERROR
        elif logstr == "critical" or logstr == "fatal":
            return log.CRITICAL
        else:
            return log.NOTSET
    
    def _loadConfig(self):
        try:
            with open('/app/config.json') as f:
                self.config = json.load(f)
                self.config['api_key'] = os.environ['API_KEY']
        except Exception as e:
            self.l.error("Failed to load config: %s" % e)
            sys.exit(1)
    
    def _setupLogger(self):
        self.l.setLevel(log.INFO)
        formatter = log.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        stdout = log.StreamHandler(sys.stdout)
        stdout.setLevel(self._interpretLogLevel(self.config['stdout']))
        stdout.addFilter(lambda record: record.levelno < log.WARNING)
        stdout.setFormatter(formatter)
        stderr = log.StreamHandler(sys.stderr)
        stderr.setLevel(self._interpretLogLevel(self.config['stderr']))
        stderr.setFormatter(formatter)
        self.l.addHandler(stdout)
        self.l.addHandler(stderr)
    
    def _signal_handler(self, sig, frame):
        if sig == signal.SIGTERM:
            self.l.info("SIGTERM received")
        elif sig == signal.SIGINT:
            self.l.info("SIGINT received")
        sys.exit(0)

    def checkIP(self):
        try:
            r = requests.get("https://myip.wtf/json")
            r.raise_for_status()
            self.ip = r.json()["YourFuckingIPAddress"]
            if self.last_ip == "":
                self.last_ip = self.ip
                self.l.info('Got IP: %s', self.ip)
                count = self.updateDNS()
                self.l.info('Updated %d records', count)
            elif self.last_ip != self.ip:
                self.l.info('IP changed from %s to %s', self.last_ip, self.ip)
                self.last_ip = self.ip
                count = self.updateDNS()
                self.l.info('Updated %d records', count)
            else:
                self.l.debug('IP unchanged: %s', self.ip)
        except Exception as e:
            self.l.error("Failed to get IP: %s" % e)
        finally:
            self.s.enter(30, 1, self.checkIP)

    def updateDNS(self):
        count = 0
        for site in self.config['domains']:
            records = self.handler._listRecords(site)
            for record in records:
                if record['type'] == 'A' and record['data'] != self.ip and record['name'] in self.config['domains'][site]:
                    if self.handler._updateRecord(site, record['id'], self.ip):
                        count += 1
        return count

if __name__ == "__main__":
    updater = DnsUpdater()
    updater.l.info('DNS Updater started')
    updater.s.enter(3, 1, updater.checkIP)
    updater.s.run()