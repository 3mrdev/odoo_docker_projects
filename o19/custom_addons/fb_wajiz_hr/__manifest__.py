{
	"name":"FireBits Wajiz HR Updates",
	"summary":"FireBits Wajiz HR Updates",
	"author":"FireBits",
	"license":"LGPL-3",
	"data":[
		"security/sec.xml",
		"security/ir.model.access.csv",
		"views/views.xml",
		"views/cron.xml",
		"reports/card.xml",
		"reports/bio_attendance.xml",
  		"reports/reports.xml",
		"data/master.xml",
		"wizard/custody.xml"
		],
	"depends":[
		'base',
		"hr",
		"hijri_islamic_calendar",
		"hr_custody",
		'hr_attendance',
		"hr_holidays",
		'hr_payroll',
		'approvals',
		'maintenance', #TODO: remove the link between hr and maintenance that mothana added
		'fleet',
		'l10n_sa_hr_payroll'
	],
	"assets": {
		"web.report_assets_common": [
			"fb_wajiz_hr/static/src/css/fonts.css"
		]
	}
}