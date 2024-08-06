--
-- This file is licensed under the Affero General Public License (AGPL) version 3.
--
-- Copyright (C) 2024 New Vector, Ltd
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Affero General Public License as
-- published by the Free Software Foundation, either version 3 of the
-- License, or (at your option) any later version.
--
-- See the GNU Affero General Public License for more details:
-- <https://www.gnu.org/licenses/agpl-3.0.html>.

CREATE TABLE delayed_events (
    delay_rowid INTEGER PRIMARY KEY, -- An alias of rowid in SQLite
    delay_id TEXT NOT NULL,
    user_localpart TEXT NOT NULL,
    running_since BIGINT NOT NULL,
    room_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    state_key TEXT,
    origin_server_ts BIGINT,
    content bytea NOT NULL,
    UNIQUE (delay_id, user_localpart)
);

CREATE INDEX delayed_events_room_state_event_idx ON delayed_events (room_id, event_type, state_key) WHERE state_key IS NOT NULL;
CREATE INDEX delayed_events_user_idx ON delayed_events (user_localpart);

CREATE TABLE delayed_event_timeouts (
    delay_rowid INTEGER PRIMARY KEY
        REFERENCES delayed_events (delay_rowid) ON DELETE CASCADE,
    delay BIGINT NOT NULL
);

CREATE TABLE delayed_event_parents (
    delay_rowid INTEGER PRIMARY KEY
        REFERENCES delayed_event_timeouts (delay_rowid) ON DELETE CASCADE
);

CREATE TABLE delayed_event_children (
    child_rowid INTEGER PRIMARY KEY
        REFERENCES delayed_events (delay_rowid) ON DELETE CASCADE,
    parent_rowid INTEGER NOT NULL
        REFERENCES delayed_event_parents (delay_rowid) ON DELETE CASCADE,
    CHECK (child_rowid <> parent_rowid)
);
