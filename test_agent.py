# test_agent.py
from agent import run_agent

print("Test 1 — Document search:")
print(run_agent("What is contiguous memory allocation?"))
print("\n" + "="*50 + "\n")

print("Test 2 — Web search:")
print(run_agent("What is the latest news about ISRO today?"))
print("\n" + "="*50 + "\n")

print("Test 3 — Calculator:")
print(run_agent("What is 15% of 85000?"))