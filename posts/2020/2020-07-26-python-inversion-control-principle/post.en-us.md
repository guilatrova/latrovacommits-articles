# Thoughts on Python Dependency Injection

The first thing that I thought that was missing when I came from a C# background to Python was:

> What should I use for Dependency Injection? How can I create interfaces?

And looks like that's a pretty common question from anyone coming from a typed language background, based on these stack overflow questions:

- https://stackoverflow.com/questions/2461702/why-is-ioc-di-not-common-in-python
- https://stackoverflow.com/questions/31678827/what-is-a-pythonic-way-for-dependency-injection
- https://stackoverflow.com/questions/156230/python-dependency-injection-framework

Please, note how all these questions mentions: _"Well, in Java..."_. Let me interrupt it right there because, **well, you're not in Java** (or C#), so how should you face this problem?

# What's Inversion of Control and why should I care about?

Let me make it simple, inversion of control states that your code should respect two rules:

- Modules should not depend on implementations, but abstractions instead;
- Implementations should depend on abstractions;

![DIP concept](dip.png)

In other words, you can achieve that in C# with something like:

```csharp
public interface IDependency {
    void work();
}

public class Implementation : IDependency {
    public void work()
    {
        Console.WriteLine("Implementation of Work!");
    }
}

public class Module() {
    private IDependency dependency;

    public Module(dependency: IDependency)
    {
        this.dependency = dependency;
    }

    public doWork()
    {
        this.dependency.work();
    }
}

```

Ok, note how `Module` knows **nothing** about `Implementation`, and how `Implementation` knows **nothing** about `Module` - Instead, both of them know only `IDependency` which can be seen as a contract between them that says: _"Hey, you should implement method `work` with no args and return `void`"_.

