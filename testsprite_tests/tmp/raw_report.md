
# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** predecirv2
- **Date:** 2026-06-29
- **Prepared by:** TestSprite AI Team

---

## 2️⃣ Requirement Validation Summary

#### Test TC001 list_all_scrapers_with_status
- **Test Code:** [TC001_list_all_scrapers_with_status.py](./TC001_list_all_scrapers_with_status.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/adaf3956-f39a-49d4-b2b5-2fd73bdcddc9/e028a364-92e3-4bbf-a511-a90fc9a7fab4
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002 execute_single_scraper_with_sse_logs
- **Test Code:** [TC002_execute_single_scraper_with_sse_logs.py](./TC002_execute_single_scraper_with_sse_logs.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sseclient'

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/adaf3956-f39a-49d4-b2b5-2fd73bdcddc9/5a61e98f-c0f6-4986-ba7c-4b2928206354
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003 handle_scraper_not_found_on_execution
- **Test Code:** [TC003_handle_scraper_not_found_on_execution.py](./TC003_handle_scraper_not_found_on_execution.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/adaf3956-f39a-49d4-b2b5-2fd73bdcddc9/8d7826f4-2b86-4299-8a7e-584d105f4bfe
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004 execute_multiple_scrapers_sequentially_with_progress
- **Test Code:** [TC004_execute_multiple_scrapers_sequentially_with_progress.py](./TC004_execute_multiple_scrapers_sequentially_with_progress.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/lang/lib/python3.12/site-packages/urllib3/response.py", line 903, in _error_catcher
    yield
  File "/var/lang/lib/python3.12/site-packages/urllib3/response.py", line 1418, in read_chunked
    self._update_chunk_length()
  File "/var/lang/lib/python3.12/site-packages/urllib3/response.py", line 1333, in _update_chunk_length
    line = self._fp.fp.readline()  # type: ignore[union-attr]
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/socket.py", line 720, in readinto
    return self._sock.recv_into(b)
           ^^^^^^^^^^^^^^^^^^^^^^^
TimeoutError: timed out

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/var/lang/lib/python3.12/site-packages/requests/models.py", line 820, in generate
    yield from self.raw.stream(chunk_size, decode_content=True)
  File "/var/lang/lib/python3.12/site-packages/urllib3/response.py", line 1250, in stream
    yield from self.read_chunked(amt, decode_content=decode_content)
  File "/var/lang/lib/python3.12/site-packages/urllib3/response.py", line 1397, in read_chunked
    with self._error_catcher():
         ^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/contextlib.py", line 158, in __exit__
    self.gen.throw(value)
  File "/var/lang/lib/python3.12/site-packages/urllib3/response.py", line 908, in _error_catcher
    raise ReadTimeoutError(self._pool, None, "Read timed out.") from e  # type: ignore[arg-type]
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
urllib3.exceptions.ReadTimeoutError: HTTPConnectionPool(host='proxy.tun.testsprite.com', port=9090): Read timed out.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<string>", line 101, in test_execute_multiple_scrapers_sequentially_with_progress
  File "<string>", line 77, in sse_events
  File "/var/lang/lib/python3.12/site-packages/requests/models.py", line 869, in iter_lines
    for chunk in self.iter_content(
                 ^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/utils.py", line 572, in stream_decode_response_unicode
    for chunk in iterator:
                 ^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/models.py", line 826, in generate
    raise ConnectionError(e)
requests.exceptions.ConnectionError: HTTPConnectionPool(host='proxy.tun.testsprite.com', port=9090): Read timed out.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 137, in <module>
  File "<string>", line 135, in test_execute_multiple_scrapers_sequentially_with_progress
AssertionError: Request failed: HTTPConnectionPool(host='proxy.tun.testsprite.com', port=9090): Read timed out.

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/adaf3956-f39a-49d4-b2b5-2fd73bdcddc9/fa3065dc-bbf8-4068-b863-644f821ef8ae
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005 preview_scraper_data_with_validation_warnings
- **Test Code:** [TC005_preview_scraper_data_with_validation_warnings.py](./TC005_preview_scraper_data_with_validation_warnings.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 534, in _make_request
    response = conn.getresponse()
               ^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/connection.py", line 571, in getresponse
    httplib_response = super().getresponse()
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/http/client.py", line 1430, in getresponse
    response.begin()
  File "/var/lang/lib/python3.12/http/client.py", line 331, in begin
    version, status, reason = self._read_status()
                              ^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/http/client.py", line 292, in _read_status
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/socket.py", line 720, in readinto
    return self._sock.recv_into(b)
           ^^^^^^^^^^^^^^^^^^^^^^^
TimeoutError: timed out

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/var/lang/lib/python3.12/site-packages/requests/adapters.py", line 667, in send
    resp = conn.urlopen(
           ^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 841, in urlopen
    retries = retries.increment(
              ^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/util/retry.py", line 490, in increment
    raise reraise(type(error), error, _stacktrace)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/util/util.py", line 39, in reraise
    raise value
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 787, in urlopen
    response = self._make_request(
               ^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 536, in _make_request
    self._raise_timeout(err=e, url=url, timeout_value=read_timeout)
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 367, in _raise_timeout
    raise ReadTimeoutError(
urllib3.exceptions.ReadTimeoutError: HTTPConnectionPool(host='proxy.tun.testsprite.com', port=9090): Read timed out. (read timeout=30)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<string>", line 26, in test_preview_scraper_data_with_validation_warnings
  File "/var/lang/lib/python3.12/site-packages/requests/api.py", line 73, in get
    return request("get", url, params=params, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/api.py", line 59, in request
    return session.request(method=method, url=url, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/sessions.py", line 589, in request
    resp = self.send(prep, **send_kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/sessions.py", line 703, in send
    r = adapter.send(request, **kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/adapters.py", line 713, in send
    raise ReadTimeout(e, request=request)
requests.exceptions.ReadTimeout: HTTPConnectionPool(host='proxy.tun.testsprite.com', port=9090): Read timed out. (read timeout=30)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 67, in <module>
  File "<string>", line 65, in test_preview_scraper_data_with_validation_warnings
AssertionError: Request failed: HTTPConnectionPool(host='proxy.tun.testsprite.com', port=9090): Read timed out. (read timeout=30)

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/adaf3956-f39a-49d4-b2b5-2fd73bdcddc9/538a8638-d94b-4353-b374-f29c1b456963
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006 export_scraper_data_in_supported_formats
- **Test Code:** [TC006_export_scraper_data_in_supported_formats.py](./TC006_export_scraper_data_in_supported_formats.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 534, in _make_request
    response = conn.getresponse()
               ^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/connection.py", line 571, in getresponse
    httplib_response = super().getresponse()
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/http/client.py", line 1430, in getresponse
    response.begin()
  File "/var/lang/lib/python3.12/http/client.py", line 331, in begin
    version, status, reason = self._read_status()
                              ^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/http/client.py", line 292, in _read_status
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/socket.py", line 720, in readinto
    return self._sock.recv_into(b)
           ^^^^^^^^^^^^^^^^^^^^^^^
TimeoutError: timed out

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/var/lang/lib/python3.12/site-packages/requests/adapters.py", line 667, in send
    resp = conn.urlopen(
           ^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 841, in urlopen
    retries = retries.increment(
              ^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/util/retry.py", line 490, in increment
    raise reraise(type(error), error, _stacktrace)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/util/util.py", line 39, in reraise
    raise value
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 787, in urlopen
    response = self._make_request(
               ^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 536, in _make_request
    self._raise_timeout(err=e, url=url, timeout_value=read_timeout)
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 367, in _raise_timeout
    raise ReadTimeoutError(
urllib3.exceptions.ReadTimeoutError: HTTPConnectionPool(host='proxy.tun.testsprite.com', port=9090): Read timed out. (read timeout=30)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<string>", line 22, in test_export_scraper_data_in_supported_formats
  File "/var/lang/lib/python3.12/site-packages/requests/api.py", line 73, in get
    return request("get", url, params=params, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/api.py", line 59, in request
    return session.request(method=method, url=url, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/sessions.py", line 589, in request
    resp = self.send(prep, **send_kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/sessions.py", line 703, in send
    r = adapter.send(request, **kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/adapters.py", line 713, in send
    raise ReadTimeout(e, request=request)
requests.exceptions.ReadTimeout: HTTPConnectionPool(host='proxy.tun.testsprite.com', port=9090): Read timed out. (read timeout=30)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 52, in <module>
  File "<string>", line 50, in test_export_scraper_data_in_supported_formats
AssertionError: Test failed: HTTPConnectionPool(host='proxy.tun.testsprite.com', port=9090): Read timed out. (read timeout=30)

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/adaf3956-f39a-49d4-b2b5-2fd73bdcddc9/adb1570a-15ba-4aca-ab9a-42f9664eebfb
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007 list_execution_history_with_pagination
- **Test Code:** [TC007_list_execution_history_with_pagination.py](./TC007_list_execution_history_with_pagination.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/adaf3956-f39a-49d4-b2b5-2fd73bdcddc9/3e5f01c8-9055-49ff-abd3-a90e36135539
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC008 add_new_scheduler_job_with_cron_expression
- **Test Code:** [TC008_add_new_scheduler_job_with_cron_expression.py](./TC008_add_new_scheduler_job_with_cron_expression.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/adaf3956-f39a-49d4-b2b5-2fd73bdcddc9/8c207dff-695c-4f88-8d95-1e1bdff11c44
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC009 pause_and_resume_scheduled_job
- **Test Code:** [TC009_pause_and_resume_scheduled_job.py](./TC009_pause_and_resume_scheduled_job.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/adaf3956-f39a-49d4-b2b5-2fd73bdcddc9/927e41ad-779a-4afd-974d-24eca63b397d
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC010 run_html_structure_diagnostic_and_compare_snapshots
- **Test Code:** [TC010_run_html_structure_diagnostic_and_compare_snapshots.py](./TC010_run_html_structure_diagnostic_and_compare_snapshots.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/adaf3956-f39a-49d4-b2b5-2fd73bdcddc9/7de31e5e-35d8-4b57-a106-ab84cdde8bde
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---


## 3️⃣ Coverage & Matching Metrics

- **60.00** of tests passed

| Requirement        | Total Tests | ✅ Passed | ❌ Failed  |
|--------------------|-------------|-----------|------------|
| ...                | ...         | ...       | ...        |
---


## 4️⃣ Key Gaps / Risks
{AI_GNERATED_KET_GAPS_AND_RISKS}
---