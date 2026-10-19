--
-- PostgreSQL database dump
--


-- Dumped from database version 16.15 (Debian 16.15-1.pgdg12+2)
-- Dumped by pg_dump version 16.15 (Debian 16.15-1.pgdg12+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: actors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.actors (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid,
    actor_type character varying(16) NOT NULL,
    display_name character varying(128) NOT NULL,
    email character varying(255),
    role character varying(64) NOT NULL,
    password_hash character varying(255),
    capability_profile character varying(64),
    preferred_model_id uuid,
    system_prompt text,
    autonomy_level character varying(8) DEFAULT 'L1'::character varying,
    consecutive_rejects integer DEFAULT 0,
    status character varying(32) DEFAULT 'IDLE'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    role_id uuid,
    job_title_id uuid,
    phone character varying(32),
    address text,
    department_id uuid,
    hired_at timestamp with time zone DEFAULT now(),
    dismissed_at timestamp with time zone,
    description text,
    extra_permissions jsonb DEFAULT '[]'::jsonb,
    CONSTRAINT actors_actor_type_check CHECK (((actor_type)::text = ANY ((ARRAY['HUMAN'::character varying, 'AI_AGENT'::character varying])::text[]))),
    CONSTRAINT actors_autonomy_level_check CHECK (((autonomy_level)::text = ANY ((ARRAY['L1'::character varying, 'L2'::character varying, 'L3'::character varying])::text[]))),
    CONSTRAINT actors_status_check CHECK (((status)::text = ANY (ARRAY['ACTIVE'::text, 'IDLE'::text, 'WORKING'::text, 'WAITING'::text, 'QUARANTINED'::text, 'DISABLED'::text])))
);


--
-- Name: agent_documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agent_documents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    agent_id uuid NOT NULL,
    file_name character varying(255) NOT NULL,
    original_name character varying(255) NOT NULL,
    file_type character varying(32) NOT NULL,
    file_size integer NOT NULL,
    storage_path character varying(512),
    extracted_text text,
    summary text,
    status character varying(32) DEFAULT 'INDEXED'::character varying,
    memory_item_id uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: approval_group_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.approval_group_members (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    group_id uuid,
    actor_id uuid,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: approval_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.approval_groups (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid,
    code character varying(64) NOT NULL,
    name character varying(128) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: artifacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifacts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    task_id uuid,
    name character varying(255) NOT NULL,
    artifact_type character varying(32) NOT NULL,
    storage_path character varying(512),
    version integer DEFAULT 1,
    content_hash character varying(128),
    produced_by_actor_id uuid,
    approval_status character varying(32) DEFAULT 'DRAFT'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT artifacts_approval_status_check CHECK (((approval_status)::text = ANY ((ARRAY['DRAFT'::character varying, 'SUBMITTED'::character varying, 'APPROVED'::character varying, 'REJECTED'::character varying, 'SUPERSEDED'::character varying])::text[])))
);


--
-- Name: audit_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid,
    actor_id uuid,
    action character varying(64) NOT NULL,
    target_type character varying(64),
    target_id character varying(64),
    payload jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid,
    project_id uuid,
    task_id uuid,
    sender_actor_id uuid,
    role character varying(16) NOT NULL,
    content text NOT NULL,
    thought_process text,
    attachments jsonb DEFAULT '[]'::jsonb,
    tokens integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    is_private boolean DEFAULT false,
    message_type character varying(32) DEFAULT 'CHAT'::character varying,
    CONSTRAINT chat_messages_role_check CHECK (((role)::text = ANY ((ARRAY['user'::character varying, 'assistant'::character varying, 'system'::character varying, 'thought'::character varying, 'tool'::character varying])::text[])))
);


--
-- Name: debate_threads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.debate_threads (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    task_id uuid,
    issue_description text NOT NULL,
    initiator_actor_id uuid,
    referee_actor_id uuid,
    status character varying(32) DEFAULT 'OPEN'::character varying,
    adr_summary text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT debate_threads_status_check CHECK (((status)::text = ANY ((ARRAY['OPEN'::character varying, 'RESOLVED'::character varying, 'ESCALATED_TO_HUMAN'::character varying])::text[])))
);


--
-- Name: departments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.departments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    name character varying(128) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: email_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.email_templates (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    code character varying(64) NOT NULL,
    name character varying(255) NOT NULL,
    subject character varying(255) NOT NULL,
    html_content text NOT NULL,
    text_content text,
    variables jsonb DEFAULT '[]'::jsonb,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: job_titles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.job_titles (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    code character varying(64) NOT NULL,
    title character varying(128) NOT NULL,
    category character varying(64) NOT NULL,
    description text,
    base_role_prompt text NOT NULL,
    required_skills jsonb DEFAULT '[]'::jsonb,
    recommended_model_code character varying(128) DEFAULT 'glm-5.3'::character varying,
    autonomy_level character varying(8) DEFAULT 'L1'::character varying,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    tenant_id uuid,
    ai_review_status character varying(32) DEFAULT 'COMPANY_LOCAL'::character varying,
    ai_review_feedback text,
    department_id uuid
);


--
-- Name: llm_calls; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_calls (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid,
    task_id uuid,
    actor_id uuid,
    model_id uuid,
    tokens_in integer DEFAULT 0,
    tokens_out integer DEFAULT 0,
    credits_cost numeric DEFAULT 0,
    latency_ms integer DEFAULT 0,
    status character varying(32) DEFAULT 'SUCCESS'::character varying,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: llm_models; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_models (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    provider_id uuid,
    model_code character varying(128) NOT NULL,
    display_name character varying(128) NOT NULL,
    model_type character varying(32) NOT NULL,
    capabilities jsonb DEFAULT '{}'::jsonb,
    context_window integer DEFAULT 131072,
    effort_coefficient numeric DEFAULT 1.0,
    status character varying(32) DEFAULT 'ACTIVE'::character varying,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: llm_providers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_providers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    code character varying(64) NOT NULL,
    name character varying(128) NOT NULL,
    base_url character varying(255) NOT NULL,
    api_style character varying(32) DEFAULT 'openai'::character varying,
    secret_ref character varying(255),
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: memory_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.memory_items (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid,
    scope character varying(16) NOT NULL,
    agent_id uuid,
    source_reference character varying(255),
    content text NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb,
    qdrant_point_id uuid,
    status character varying(32) DEFAULT 'APPROVED'::character varying,
    confidence_score numeric DEFAULT 1.0,
    embedding_model_version character varying(64) DEFAULT 'qwen3-embedding-8b'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT memory_items_scope_check CHECK (((scope)::text = ANY ((ARRAY['GLOBAL'::character varying, 'AGENT'::character varying])::text[]))),
    CONSTRAINT memory_items_status_check CHECK (((status)::text = ANY ((ARRAY['CANDIDATE'::character varying, 'APPROVED'::character varying, 'REVOKED'::character varying])::text[])))
);


--
-- Name: nace_catalog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nace_catalog (
    code character varying(16) NOT NULL,
    title text NOT NULL,
    sector_group character varying(64) DEFAULT 'GENEL'::character varying,
    description text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: notification_schedules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notification_schedules (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(255) NOT NULL,
    trigger_type character varying(64) NOT NULL,
    template_code character varying(64) NOT NULL,
    frequency_days integer DEFAULT 15,
    target_lead_days integer DEFAULT 90,
    is_active boolean DEFAULT true,
    last_run_at timestamp with time zone,
    next_run_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plans (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    code character varying(64) NOT NULL,
    name character varying(128) NOT NULL,
    description text,
    monthly_price numeric DEFAULT 0.0,
    currency character varying(8) DEFAULT 'TRY'::character varying,
    max_humans integer DEFAULT 5,
    max_agents integer DEFAULT 5,
    max_projects integer DEFAULT 3,
    monthly_credits integer DEFAULT 1000,
    storage_gb integer DEFAULT 10,
    allowed_models jsonb DEFAULT '[]'::jsonb,
    features jsonb DEFAULT '{}'::jsonb,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    can_create_custom_titles boolean DEFAULT false
);


--
-- Name: professions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.professions (
    code character varying(32) NOT NULL,
    sector_code character varying(32) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projects (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid,
    slug character varying(64) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    field_package character varying(32) DEFAULT 'GENEL'::character varying,
    status character varying(32) DEFAULT 'DRAFT'::character varying,
    repo_url character varying(255),
    created_by_actor_id uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT projects_status_check CHECK (((status)::text = ANY ((ARRAY['DRAFT'::character varying, 'PROVISIONING'::character varying, 'READY'::character varying, 'ACTIVE'::character varying, 'RELEASE_PENDING'::character varying, 'RELEASED'::character varying, 'PROVISION_FAILED'::character varying, 'PAUSED'::character varying, 'CANCELLED'::character varying])::text[])))
);


--
-- Name: sector_definitions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sector_definitions (
    id uuid NOT NULL,
    code character varying(64) NOT NULL,
    name character varying(128) NOT NULL,
    description text,
    icon character varying(32),
    default_nace_codes jsonb,
    is_active boolean,
    display_order integer,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: sectors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sectors (
    code character varying(32) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    icon text,
    image_url text
);


--
-- Name: system_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_permissions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    code character varying(64) NOT NULL,
    module character varying(64) NOT NULL,
    name character varying(128) NOT NULL,
    description text,
    default_for_roles jsonb DEFAULT '[]'::jsonb,
    is_system boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: system_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_settings (
    key character varying(64) NOT NULL,
    value jsonb NOT NULL,
    description text,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tasks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid,
    title character varying(255) NOT NULL,
    description text,
    acceptance_criteria text,
    priority character varying(16) DEFAULT 'MEDIUM'::character varying,
    status character varying(32) DEFAULT 'BACKLOG'::character varying,
    assignee_actor_id uuid,
    estimated_effort numeric DEFAULT 1.0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT tasks_priority_check CHECK (((priority)::text = ANY ((ARRAY['LOW'::character varying, 'MEDIUM'::character varying, 'HIGH'::character varying, 'CRITICAL'::character varying])::text[]))),
    CONSTRAINT tasks_status_check CHECK (((status)::text = ANY ((ARRAY['BACKLOG'::character varying, 'READY'::character varying, 'IN_PROGRESS'::character varying, 'WAITING_APPROVAL'::character varying, 'IN_DEBATE'::character varying, 'REVISION'::character varying, 'DONE'::character varying, 'BLOCKED'::character varying, 'QUARANTINED'::character varying, 'CANCELLED'::character varying, 'FAILED'::character varying, 'TIMED_OUT'::character varying])::text[])))
);


--
-- Name: tenant_leads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tenant_leads (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    plan_id uuid,
    company_name character varying(255) NOT NULL,
    tax_id character varying(32),
    address text,
    phone character varying(32),
    website character varying(255),
    contact_email character varying(255) NOT NULL,
    nace_codes jsonb DEFAULT '[]'::jsonb,
    generated_manifesto text,
    assigned_skills jsonb DEFAULT '[]'::jsonb,
    status character varying(32) DEFAULT 'PENDING'::character varying,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    odoo_partner_id integer,
    odoo_order_id integer,
    odoo_order_name character varying(64),
    tax_office character varying(128),
    sectors jsonb DEFAULT '[]'::jsonb,
    professions jsonb DEFAULT '[]'::jsonb,
    CONSTRAINT tenant_leads_status_check CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'CONTACTED'::character varying, 'APPROVED'::character varying, 'REJECTED'::character varying])::text[])))
);


--
-- Name: tenant_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tenant_roles (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid,
    name character varying(64) NOT NULL,
    description text,
    permissions jsonb DEFAULT '[]'::jsonb,
    is_system boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: tenants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tenants (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    slug character varying(64) NOT NULL,
    name character varying(255) NOT NULL,
    tax_id character varying(64),
    nace_codes jsonb DEFAULT '[]'::jsonb,
    sector_manifesto text,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    phone character varying(32),
    address text,
    website character varying(255),
    contact_email character varying(255),
    plan_id uuid,
    tax_office character varying(128),
    package_start_date timestamp with time zone DEFAULT now(),
    package_expiry_date timestamp with time zone DEFAULT (now() + '1 year'::interval),
    last_reminder_sent_at timestamp with time zone,
    sectors jsonb DEFAULT '[]'::jsonb,
    professions jsonb DEFAULT '[]'::jsonb
);


--
-- Name: actors actors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actors
    ADD CONSTRAINT actors_pkey PRIMARY KEY (id);


--
-- Name: agent_documents agent_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_documents
    ADD CONSTRAINT agent_documents_pkey PRIMARY KEY (id);


--
-- Name: approval_group_members approval_group_members_group_id_actor_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_group_members
    ADD CONSTRAINT approval_group_members_group_id_actor_id_key UNIQUE (group_id, actor_id);


--
-- Name: approval_group_members approval_group_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_group_members
    ADD CONSTRAINT approval_group_members_pkey PRIMARY KEY (id);


--
-- Name: approval_groups approval_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_groups
    ADD CONSTRAINT approval_groups_pkey PRIMARY KEY (id);


--
-- Name: approval_groups approval_groups_tenant_id_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_groups
    ADD CONSTRAINT approval_groups_tenant_id_code_key UNIQUE (tenant_id, code);


--
-- Name: artifacts artifacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifacts
    ADD CONSTRAINT artifacts_pkey PRIMARY KEY (id);


--
-- Name: audit_events audit_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: debate_threads debate_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.debate_threads
    ADD CONSTRAINT debate_threads_pkey PRIMARY KEY (id);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (id);


--
-- Name: email_templates email_templates_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_templates
    ADD CONSTRAINT email_templates_code_key UNIQUE (code);


--
-- Name: email_templates email_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_templates
    ADD CONSTRAINT email_templates_pkey PRIMARY KEY (id);


--
-- Name: job_titles job_titles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_titles
    ADD CONSTRAINT job_titles_pkey PRIMARY KEY (id);


--
-- Name: llm_calls llm_calls_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_calls
    ADD CONSTRAINT llm_calls_pkey PRIMARY KEY (id);


--
-- Name: llm_models llm_models_model_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_models
    ADD CONSTRAINT llm_models_model_code_key UNIQUE (model_code);


--
-- Name: llm_models llm_models_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_models
    ADD CONSTRAINT llm_models_pkey PRIMARY KEY (id);


--
-- Name: llm_providers llm_providers_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_providers
    ADD CONSTRAINT llm_providers_code_key UNIQUE (code);


--
-- Name: llm_providers llm_providers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_providers
    ADD CONSTRAINT llm_providers_pkey PRIMARY KEY (id);


--
-- Name: memory_items memory_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.memory_items
    ADD CONSTRAINT memory_items_pkey PRIMARY KEY (id);


--
-- Name: nace_catalog nace_catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nace_catalog
    ADD CONSTRAINT nace_catalog_pkey PRIMARY KEY (code);


--
-- Name: notification_schedules notification_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_schedules
    ADD CONSTRAINT notification_schedules_pkey PRIMARY KEY (id);


--
-- Name: plans plans_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plans
    ADD CONSTRAINT plans_code_key UNIQUE (code);


--
-- Name: plans plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plans
    ADD CONSTRAINT plans_pkey PRIMARY KEY (id);


--
-- Name: professions professions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.professions
    ADD CONSTRAINT professions_pkey PRIMARY KEY (code);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: projects projects_tenant_id_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_tenant_id_slug_key UNIQUE (tenant_id, slug);


--
-- Name: sector_definitions sector_definitions_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sector_definitions
    ADD CONSTRAINT sector_definitions_code_key UNIQUE (code);


--
-- Name: sector_definitions sector_definitions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sector_definitions
    ADD CONSTRAINT sector_definitions_pkey PRIMARY KEY (id);


--
-- Name: sectors sectors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sectors
    ADD CONSTRAINT sectors_pkey PRIMARY KEY (code);


--
-- Name: system_permissions system_permissions_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_permissions
    ADD CONSTRAINT system_permissions_code_key UNIQUE (code);


--
-- Name: system_permissions system_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_permissions
    ADD CONSTRAINT system_permissions_pkey PRIMARY KEY (id);


--
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (key);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: tenant_leads tenant_leads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tenant_leads
    ADD CONSTRAINT tenant_leads_pkey PRIMARY KEY (id);


--
-- Name: tenant_roles tenant_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tenant_roles
    ADD CONSTRAINT tenant_roles_pkey PRIMARY KEY (id);


--
-- Name: tenants tenants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_pkey PRIMARY KEY (id);


--
-- Name: tenants tenants_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_slug_key UNIQUE (slug);


--
-- Name: idx_agent_documents_agent_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_agent_documents_agent_id ON public.agent_documents USING btree (agent_id);


--
-- Name: idx_agent_documents_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_agent_documents_tenant_id ON public.agent_documents USING btree (tenant_id);


--
-- Name: idx_chat_messages_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_messages_project_id ON public.chat_messages USING btree (project_id, created_at);


--
-- Name: idx_chat_messages_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_messages_task_id ON public.chat_messages USING btree (task_id, created_at);


--
-- Name: idx_departments_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_departments_tenant_id ON public.departments USING btree (tenant_id);


--
-- Name: idx_nace_catalog_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nace_catalog_code ON public.nace_catalog USING btree (code);


--
-- Name: idx_professions_sector_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_professions_sector_code ON public.professions USING btree (sector_code);


--
-- Name: idx_tenant_leads_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tenant_leads_status ON public.tenant_leads USING btree (status);


--
-- Name: idx_tenant_roles_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tenant_roles_tenant_id ON public.tenant_roles USING btree (tenant_id);


--
-- Name: uq_departments_tenant_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_departments_tenant_name ON public.departments USING btree (tenant_id, lower((name)::text));


--
-- Name: uq_job_titles_tenant_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_job_titles_tenant_code ON public.job_titles USING btree (COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), lower((code)::text));


--
-- Name: actors actors_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actors
    ADD CONSTRAINT actors_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: actors actors_job_title_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actors
    ADD CONSTRAINT actors_job_title_id_fkey FOREIGN KEY (job_title_id) REFERENCES public.job_titles(id) ON DELETE SET NULL;


--
-- Name: actors actors_preferred_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actors
    ADD CONSTRAINT actors_preferred_model_id_fkey FOREIGN KEY (preferred_model_id) REFERENCES public.llm_models(id) ON DELETE SET NULL;


--
-- Name: actors actors_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actors
    ADD CONSTRAINT actors_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.tenant_roles(id) ON DELETE SET NULL;


--
-- Name: actors actors_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actors
    ADD CONSTRAINT actors_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: agent_documents agent_documents_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_documents
    ADD CONSTRAINT agent_documents_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.actors(id) ON DELETE CASCADE;


--
-- Name: agent_documents agent_documents_memory_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_documents
    ADD CONSTRAINT agent_documents_memory_item_id_fkey FOREIGN KEY (memory_item_id) REFERENCES public.memory_items(id) ON DELETE SET NULL;


--
-- Name: agent_documents agent_documents_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_documents
    ADD CONSTRAINT agent_documents_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: approval_group_members approval_group_members_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_group_members
    ADD CONSTRAINT approval_group_members_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES public.actors(id) ON DELETE CASCADE;


--
-- Name: approval_group_members approval_group_members_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_group_members
    ADD CONSTRAINT approval_group_members_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.approval_groups(id) ON DELETE CASCADE;


--
-- Name: approval_groups approval_groups_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_groups
    ADD CONSTRAINT approval_groups_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: artifacts artifacts_produced_by_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifacts
    ADD CONSTRAINT artifacts_produced_by_actor_id_fkey FOREIGN KEY (produced_by_actor_id) REFERENCES public.actors(id) ON DELETE SET NULL;


--
-- Name: artifacts artifacts_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifacts
    ADD CONSTRAINT artifacts_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: audit_events audit_events_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES public.actors(id) ON DELETE SET NULL;


--
-- Name: audit_events audit_events_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: chat_messages chat_messages_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: chat_messages chat_messages_sender_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_sender_actor_id_fkey FOREIGN KEY (sender_actor_id) REFERENCES public.actors(id) ON DELETE SET NULL;


--
-- Name: chat_messages chat_messages_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: chat_messages chat_messages_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: debate_threads debate_threads_initiator_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.debate_threads
    ADD CONSTRAINT debate_threads_initiator_actor_id_fkey FOREIGN KEY (initiator_actor_id) REFERENCES public.actors(id) ON DELETE SET NULL;


--
-- Name: debate_threads debate_threads_referee_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.debate_threads
    ADD CONSTRAINT debate_threads_referee_actor_id_fkey FOREIGN KEY (referee_actor_id) REFERENCES public.actors(id) ON DELETE SET NULL;


--
-- Name: debate_threads debate_threads_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.debate_threads
    ADD CONSTRAINT debate_threads_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: departments departments_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: job_titles job_titles_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_titles
    ADD CONSTRAINT job_titles_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: job_titles job_titles_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_titles
    ADD CONSTRAINT job_titles_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: llm_calls llm_calls_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_calls
    ADD CONSTRAINT llm_calls_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES public.actors(id) ON DELETE SET NULL;


--
-- Name: llm_calls llm_calls_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_calls
    ADD CONSTRAINT llm_calls_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.llm_models(id) ON DELETE SET NULL;


--
-- Name: llm_calls llm_calls_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_calls
    ADD CONSTRAINT llm_calls_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE SET NULL;


--
-- Name: llm_calls llm_calls_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_calls
    ADD CONSTRAINT llm_calls_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: llm_models llm_models_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_models
    ADD CONSTRAINT llm_models_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.llm_providers(id) ON DELETE CASCADE;


--
-- Name: memory_items memory_items_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.memory_items
    ADD CONSTRAINT memory_items_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.actors(id) ON DELETE CASCADE;


--
-- Name: memory_items memory_items_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.memory_items
    ADD CONSTRAINT memory_items_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: professions professions_sector_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.professions
    ADD CONSTRAINT professions_sector_code_fkey FOREIGN KEY (sector_code) REFERENCES public.sectors(code) ON DELETE CASCADE;


--
-- Name: projects projects_created_by_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_created_by_actor_id_fkey FOREIGN KEY (created_by_actor_id) REFERENCES public.actors(id) ON DELETE SET NULL;


--
-- Name: projects projects_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: tasks tasks_assignee_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_assignee_actor_id_fkey FOREIGN KEY (assignee_actor_id) REFERENCES public.actors(id) ON DELETE SET NULL;


--
-- Name: tasks tasks_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: tenant_leads tenant_leads_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tenant_leads
    ADD CONSTRAINT tenant_leads_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.plans(id) ON DELETE SET NULL;


--
-- Name: tenant_roles tenant_roles_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tenant_roles
    ADD CONSTRAINT tenant_roles_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: tenants tenants_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.plans(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--


