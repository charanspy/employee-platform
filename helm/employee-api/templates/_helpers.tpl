{{- define "employee-api.fullname" -}}
{{ .Release.Name }}-{{ .Chart.Name }}
{{- end }}
