import importlib
import os
import unittest


def discover_and_import_tests(start_dir="."):
    suite = unittest.TestSuite()
    for root, dirs, files in os.walk(start_dir):
        for file_name in files:
            if file_name.startswith("test_") and file_name.endswith(".py"):
                # Construct the module name by removing the ".py" extension
                relative_path = os.path.relpath(
                    os.path.join(root, file_name), start=start_dir
                )
                module_name = os.path.splitext(relative_path.replace(os.path.sep, "."))[
                    0
                ]
                # Build the relative path to the module
                relative_path = os.path.relpath(
                    os.path.join(root, file_name), start=start_dir
                )
                print("Importing", module_name, relative_path)
                # Import the module dynamically
                test_module = importlib.import_module(module_name)

                # Iterate through the attributes of the module
                for name in dir(test_module):
                    obj = getattr(test_module, name)
                    # Check if the attribute is a class and a subclass of unittest.TestCase
                    if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
                        # Add the test class to the suite
                        suite.addTest(
                            unittest.defaultTestLoader.loadTestsFromTestCase(obj)
                        )
    return suite


if __name__ == "__main__":
    # Run the dynamically discovered test suite
    runner = unittest.TextTestRunner(verbosity=2)
    tests = discover_and_import_tests()
    print("Testing now!!!!")
    result = runner.run(tests)
