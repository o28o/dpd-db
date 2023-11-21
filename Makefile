test:
	export TODAY=2023-11-20 && pytest

time_log.png:
	@gnuplot < tools/time_log.gp
