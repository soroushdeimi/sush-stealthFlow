{{/*
Expand the name of the chart.
*/}}
{{- define "stealthflow.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "stealthflow.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "stealthflow.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "stealthflow.labels" -}}
helm.sh/chart: {{ include "stealthflow.chart" . }}
{{ include "stealthflow.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "stealthflow.selectorLabels" -}}
app.kubernetes.io/name: {{ include "stealthflow.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "stealthflow.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "stealthflow.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate UUID if not provided
*/}}
{{- define "stealthflow.uuid" -}}
{{- if .Values.secrets.uuid }}
{{- .Values.secrets.uuid }}
{{- else }}
{{- uuidv4 }}
{{- end }}
{{- end }}

{{/*
Generate random password if not provided
*/}}
{{- define "stealthflow.trojanPassword" -}}
{{- if .Values.secrets.trojanPassword }}
{{- .Values.secrets.trojanPassword }}
{{- else }}
{{- randAlphaNum 32 | b64enc }}
{{- end }}
{{- end }}

{{/*
Signaling labels
*/}}
{{- define "stealthflow.signaling.labels" -}}
helm.sh/chart: {{ include "stealthflow.chart" . }}
{{ include "stealthflow.signaling.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Signaling selector labels
*/}}
{{- define "stealthflow.signaling.selectorLabels" -}}
app.kubernetes.io/name: {{ include "stealthflow.name" . }}-signaling
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
