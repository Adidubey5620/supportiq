import asyncio

from supportiq.services.ai import generate_support_reply


async def main():
    customer_message = (
        "I cannot log in to my account. "
        "I tried resetting my password, but I haven't received an email."
    )

    print("Customer message:")
    print(customer_message)

    print("\nGenerating AI response...\n")

    try:
        reply = await generate_support_reply(customer_message)
        print("SupportIQ suggested reply:")
        print(reply)
    except Exception as exc:
        print(f"AI request failed: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
