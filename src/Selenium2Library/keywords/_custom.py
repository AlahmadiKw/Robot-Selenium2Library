import os
from functools import wraps
from retrying import retry
from keywordgroup import KeywordGroup
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException

template = "An exception of type {0} occured. Arguments:\n{1!r}"

def retry_if_value_error(exception):
    return isinstance(exception, ValueError)

def searchframes(func):
    @wraps(func)
    def func_wrapper(self, *args):
        try:
            return func(self, *args)
        except (WebDriverException, ValueError) as ex:
            self._debug("Failed to locate element. Searching in frames...")
            message = template.format(type(ex).__name__, ex.args)
            self._debug(message)

        def _traverse_frames(self, frame_path, found, func_return=None, c=0):
            # https://groups.google.com/forum/#!topic/webdriver/OYh9mLtLdeo
            # http://stackoverflow.com/questions/16166261/selenium-webdriver-stale-element-reference-exception
            if found:
                return (found, func_return)

            browser = self._current_browser()

            subframes = self._element_find("xpath=//frame|//iframe", False, False)
            self._debug("traverseing %d frames... " % len(subframes))

            try:
                func_return = func(self, *args)
                browser.switch_to_default_content()
                found = True
                return (found, func_return)
            except (WebDriverException, ValueError) as ex:
                self._debug("offf Failed to locate element at this frame.")
                message = template.format(type(ex).__name__, ex.args)
                self._debug(message)

            if len(subframes)>0:
                for ifr in subframes:
                    browser.switch_to_default_content()
                    for frame in frame_path:
                        try:
                            browser.switch_to_frame(frame)
                        except StaleElementReferenceException:
                            return False
                    try:
                        browser.switch_to_frame(ifr)
                    except StaleElementReferenceException:
                        return False
                    frame_path.append(ifr)
                    (found, func_return) = _traverse_frames(self, frame_path, found, func_return, c)
                    frame_path.remove(ifr)

            return (found, func_return)

        (success, func_return) = _traverse_frames(self, [], False)
        if not success:
            self._current_browser().switch_to_default_content()
            raise ValueError("Element locator did not found in any frames.")

        return func_return

    return func_wrapper



# def searchframes(func):
#     @wraps(func)
#     def func_wrapper(self, *args):

#         try:
#             func(self, *args)
#             return
#         except Exception as ex:
#             self._debug("Failed to locate element. Searching in frames...")
#             template = "An exception of type {0} occured. Arguments:\n{1!r}"
#             message = template.format(type(ex).__name__, ex.args)
#             self._debug(message)

#         browser = self._current_browser()
#         browser.switch_to_default_content()

#         subframes = self._element_find("xpath=//frame|//iframe", False, False)
#         self._debug('Current frame has %d subframes omg' % len(subframes))
#         for frame in subframes:
#             browser.switch_to_frame(frame)
#             try:
#                 func(self, *args)
#                 browser.switch_to_default_content()
#                 return
#             except Exception as ex:
#                 self._debug("Failed to locate element in this frame...")
#                 template = "An exception of type {0} occured. Arguments:\n{1!r}"
#                 message = template.format(type(ex).__name__, ex.args)
#                 self._debug(message)

#         browser.switch_to_default_content()
#         raise ValueError("Element locator '" + locator + "' did not found in any frames.")
#     return func_wrapper
