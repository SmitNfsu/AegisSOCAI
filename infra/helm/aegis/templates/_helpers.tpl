{{/*
Expand the name of the chart.
*/}}
{{- define "aegis.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a fully qualified app name.
*/}}
{{- define "aegis.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Chart label (chart+version).
*/}}
{{- define "aegis.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels.
*/}}
{{- define "aegis.labels" -}}
helm.sh/chart: {{ include "aegis.chart" . }}
{{ include "aegis.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: aegis
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{/*
Selector labels.
*/}}
{{- define "aegis.selectorLabels" -}}
app.kubernetes.io/name: {{ include "aegis.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Per-component names and labels.
*/}}
{{- define "aegis.backend.fullname" -}}
{{- printf "%s-backend" (include "aegis.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "aegis.daemon.fullname" -}}
{{- printf "%s-daemon" (include "aegis.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "aegis.llmWorker.fullname" -}}
{{- printf "%s-llm-worker" (include "aegis.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "aegis.agentWorker.fullname" -}}
{{- printf "%s-agent-worker" (include "aegis.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "aegis.agentServe.fullname" -}}
{{- printf "%s-agent-serve" (include "aegis.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "aegis.postgres.fullname" -}}
{{- printf "%s-postgres" (include "aegis.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "aegis.redis.fullname" -}}
{{- printf "%s-redis" (include "aegis.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "aegis.dbInit.fullname" -}}
{{- printf "%s-db-init" (include "aegis.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "aegis.configmap.fullname" -}}
{{- printf "%s-config" (include "aegis.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "aegis.secret.fullname" -}}
{{- if .Values.secrets.existingSecret -}}
{{- .Values.secrets.existingSecret -}}
{{- else -}}
{{- printf "%s-secrets" (include "aegis.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Per-component selector labels. Usage:
  {{- include "aegis.componentSelectorLabels" (dict "context" . "component" "backend") | nindent 4 }}
*/}}
{{- define "aegis.componentSelectorLabels" -}}
{{- $ctx := .context -}}
{{ include "aegis.selectorLabels" $ctx }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{/*
Per-component labels (selector + common).
*/}}
{{- define "aegis.componentLabels" -}}
{{- $ctx := .context -}}
{{ include "aegis.labels" $ctx }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{/*
Service account name.
*/}}
{{- define "aegis.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "aegis.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
Resolve an image reference for the given component.
Usage: {{ include "aegis.image" (dict "context" . "component" "backend") }}
Falls back to global.imageNamespace + "-<component>" when repository is empty.
The "llmWorker" component always reuses the backend image.
*/}}
{{- define "aegis.image" -}}
{{- $ctx := .context -}}
{{- $comp := .component -}}
{{- $compValues := get $ctx.Values $comp -}}
{{- $repo := "" -}}
{{- $tag := "" -}}
{{- $pullPolicy := "" -}}
{{- if $compValues -}}
  {{- $img := get $compValues "image" | default dict -}}
  {{- $repo = get $img "repository" | default "" -}}
  {{- $tag = get $img "tag" | default "" -}}
  {{- $pullPolicy = get $img "pullPolicy" | default "" -}}
{{- end -}}
{{- /* llm-worker reuses the backend image when not set explicitly */ -}}
{{- if and (eq $comp "llmWorker") (eq $repo "") -}}
  {{- $backendImg := $ctx.Values.backend.image | default dict -}}
  {{- $repo = get $backendImg "repository" | default "" -}}
  {{- if eq $tag "" -}}{{- $tag = get $backendImg "tag" | default "" -}}{{- end -}}
{{- end -}}
{{- /* Auto-derive repository from global.imageNamespace when still empty. */ -}}
{{- if eq $repo "" -}}
  {{- $registry := $ctx.Values.global.imageRegistry -}}
  {{- $ns := $ctx.Values.global.imageNamespace -}}
  {{- /* Map the chart component names to image suffixes */ -}}
  {{- $suffix := "backend" -}}
  {{- if eq $comp "daemon" -}}{{- $suffix = "daemon" -}}{{- end -}}
  {{- if eq $comp "backend" -}}{{- $suffix = "backend" -}}{{- end -}}
  {{- if eq $comp "llmWorker" -}}{{- $suffix = "backend" -}}{{- end -}}
  {{- /* The agent layer is Node, not Python — it cannot reuse the backend
         image the way llm-worker does, and the default above would silently
         hand it one. Both components share the one image and differ only in
         which command the Deployment runs (infra/docker/Dockerfile.agent). */ -}}
  {{- if eq $comp "agentWorker" -}}{{- $suffix = "agent" -}}{{- end -}}
  {{- if eq $comp "agentServe" -}}{{- $suffix = "agent" -}}{{- end -}}
  {{- $repo = printf "%s/%s-%s" $registry $ns $suffix -}}
{{- end -}}
{{- if eq $tag "" -}}
  {{- $tag = $ctx.Chart.AppVersion | toString -}}
{{- end -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end -}}

{{/*
Resolve image pull policy for a component, inheriting from global.
*/}}
{{- define "aegis.imagePullPolicy" -}}
{{- $ctx := .context -}}
{{- $comp := .component -}}
{{- $compValues := get $ctx.Values $comp | default dict -}}
{{- $img := get $compValues "image" | default dict -}}
{{- $pp := get $img "pullPolicy" | default "" -}}
{{- if eq $pp "" -}}
  {{- $pp = $ctx.Values.global.imagePullPolicy | default "IfNotPresent" -}}
{{- end -}}
{{- $pp -}}
{{- end -}}

{{/*
Image pull secrets list.
*/}}
{{- define "aegis.imagePullSecrets" -}}
{{- with .Values.global.imagePullSecrets }}
imagePullSecrets:
{{- toYaml . | nindent 2 }}
{{- end }}
{{- end -}}

{{/*
Postgres host/port/database resolution. Three modes:
  1. MVP in-chart StatefulSet (postgresql.enabled=true, bitnami.enabled=false)
  2. Bitnami postgresql subchart (postgresql.bitnami.enabled=true)
  3. External DB (postgresql.enabled=false)
*/}}
{{- define "aegis.postgres.host" -}}
{{- if .Values.postgresql.bitnami.enabled -}}
{{- .Values.postgresql.bitnami.fullnameOverride | default (printf "%s-postgresql" .Release.Name) -}}
{{- else if .Values.postgresql.enabled -}}
{{ include "aegis.postgres.fullname" . }}
{{- else -}}
{{- required "postgresql.external.host is required when postgresql.enabled=false and postgresql.bitnami.enabled=false" .Values.postgresql.external.host -}}
{{- end -}}
{{- end -}}

{{- define "aegis.postgres.port" -}}
{{- if .Values.postgresql.bitnami.enabled -}}
{{- .Values.postgresql.bitnami.primary.service.ports.postgresql | default 5432 -}}
{{- else if .Values.postgresql.enabled -}}
{{- .Values.postgresql.service.port | default 5432 -}}
{{- else -}}
{{- .Values.postgresql.external.port | default 5432 -}}
{{- end -}}
{{- end -}}

{{- define "aegis.postgres.database" -}}
{{- if .Values.postgresql.bitnami.enabled -}}
{{- .Values.postgresql.bitnami.auth.database | default "deeptempo_soc" -}}
{{- else if .Values.postgresql.enabled -}}
{{- .Values.postgresql.auth.database | default "deeptempo_soc" -}}
{{- else -}}
{{- .Values.postgresql.external.database | default "deeptempo_soc" -}}
{{- end -}}
{{- end -}}

{{- define "aegis.postgres.username" -}}
{{- if .Values.postgresql.bitnami.enabled -}}
{{- .Values.postgresql.bitnami.auth.username | default "deeptempo" -}}
{{- else if .Values.postgresql.enabled -}}
{{- .Values.postgresql.auth.username | default "deeptempo" -}}
{{- else -}}
{{- .Values.postgresql.external.username | default "deeptempo" -}}
{{- end -}}
{{- end -}}

{{/*
Name of the secret holding POSTGRES_PASSWORD. Bitnami emits its own secret
(<release>-postgresql) with key `password` for the non-superuser; the backend
needs to pick that up.
*/}}
{{- define "aegis.postgres.passwordSecret" -}}
{{- if .Values.postgresql.bitnami.enabled -}}
{{- if .Values.postgresql.bitnami.auth.existingSecret -}}
{{- .Values.postgresql.bitnami.auth.existingSecret -}}
{{- else -}}
{{- .Values.postgresql.bitnami.fullnameOverride | default (printf "%s-postgresql" .Release.Name) -}}
{{- end -}}
{{- else if .Values.postgresql.enabled -}}
{{- if .Values.postgresql.auth.existingSecret -}}
{{- .Values.postgresql.auth.existingSecret -}}
{{- else -}}
{{- include "aegis.secret.fullname" . -}}
{{- end -}}
{{- else -}}
{{- if .Values.postgresql.external.existingSecret -}}
{{- .Values.postgresql.external.existingSecret -}}
{{- else -}}
{{- include "aegis.secret.fullname" . -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "aegis.postgres.passwordSecretKey" -}}
{{- if .Values.postgresql.bitnami.enabled -}}
{{- /* Bitnami postgresql secret key is "password" for the non-superuser. */ -}}
{{- .Values.postgresql.bitnami.auth.secretKeys.userPasswordKey | default "password" -}}
{{- else if .Values.postgresql.enabled -}}
{{- .Values.postgresql.auth.existingSecretKey | default "POSTGRES_PASSWORD" -}}
{{- else -}}
{{- .Values.postgresql.external.existingSecretKey | default "POSTGRES_PASSWORD" -}}
{{- end -}}
{{- end -}}

{{/*
REDIS_URL resolution. Same three modes as Postgres.

Bitnami redis defaults to password auth on — we pull the password from the
subchart's emitted secret at runtime via env-var substitution, so the URL
template here uses the $(REDIS_PASSWORD) placeholder which Kubernetes
expands from envFrom/env.
*/}}
{{- define "aegis.redis.url" -}}
{{- $db := include "aegis.redis.database" . -}}
{{- if .Values.redis.bitnami.enabled -}}
{{- $host := .Values.redis.bitnami.fullnameOverride | default (printf "%s-redis-master" .Release.Name) -}}
{{- $port := 6379 -}}
{{- if .Values.redis.bitnami.auth.enabled -}}
{{- printf "redis://:$(REDIS_PASSWORD)@%s:%v/%s" $host $port $db -}}
{{- else -}}
{{- printf "redis://%s:%v/%s" $host $port $db -}}
{{- end -}}
{{- else if .Values.redis.external.url -}}
{{- .Values.redis.external.url -}}
{{- else if .Values.redis.enabled -}}
{{- printf "redis://%s:%v/%s" (include "aegis.redis.fullname" .) (.Values.redis.service.port | default 6379) $db -}}
{{- else -}}
{{- required "redis.external.url is required when redis.enabled=false and redis.bitnami.enabled=false" "" -}}
{{- end -}}
{{- end -}}

{{/*
One definition because three have to agree: the URL above, the agent pods' REDIS_DB
and the KEDA scaler's databaseIndex — a scaler counting a different database reads
an empty queue. Does not govern redis.external.url, whose database that URL names.
*/}}
{{- define "aegis.redis.database" -}}
0
{{- end -}}

{{/*
Bitnami Redis password secret — used by app pods to resolve REDIS_PASSWORD.
*/}}
{{- define "aegis.redis.bitnami.passwordSecret" -}}
{{- if .Values.redis.bitnami.auth.existingSecret -}}
{{- .Values.redis.bitnami.auth.existingSecret -}}
{{- else -}}
{{- .Values.redis.bitnami.fullnameOverride | default (printf "%s-redis" .Release.Name) -}}
{{- end -}}
{{- end -}}

{{- define "aegis.redis.bitnami.passwordSecretKey" -}}
{{- .Values.redis.bitnami.auth.existingSecretPasswordKey | default "redis-password" -}}
{{- end -}}

{{/*
Is an external Redis URL stored in a secret?
*/}}
{{- define "aegis.redis.urlFromSecret" -}}
{{- if and .Values.redis.external.existingSecret (not .Values.redis.enabled) -}}
true
{{- end -}}
{{- end -}}
