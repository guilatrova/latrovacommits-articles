async def anyfunc():
     return 1

r = anyfunc()
print(type(r))
# Output: <class 'coroutine'>
