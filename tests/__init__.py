#
# This file is licensed under the Affero General Public License (AGPL) version 3.
#
# Copyright 2014-2016 OpenMarket Ltd
# Copyright (C) 2023 New Vector, Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# See the GNU Affero General Public License for more details:
# <https://www.gnu.org/licenses/agpl-3.0.html>.
#
# Originally licensed under the Apache License, Version 2.0:
# <http://www.apache.org/licenses/LICENSE-2.0>.
#
# [This file includes modifications made by New Vector Limited]
#
#

try:
	from twisted.trial import util
	from synapse.util.patch_inline_callbacks import do_patch

	# attempt to do the patch before we load any synapse code
	do_patch()

	util.DEFAULT_TIMEOUT_DURATION = 20
except Exception:
	# Twisted or synapse patching not available in this environment.
	# Tests that depend on those frameworks will need the proper deps.
	# We provide a no-op fallback so individual lightweight tests can run.
	class _DummyUtil:
		DEFAULT_TIMEOUT_DURATION = 20

	util = _DummyUtil()
