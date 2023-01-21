from kh_common.config.constants import Environment, environment


CONSTANTS = {
	Environment.test: {
		'Host': '',
	},
	Environment.local: {
		'Host': 'http://localhost:5005',
	},
	Environment.dev: {
		'Host': 'https://users-dev.fuzz.ly',
	},
	Environment.prod: {
		'Host': 'https://users.fuzz.ly',
	},
}


locals().update(CONSTANTS[environment])


del CONSTANTS
