def camel_case_to_snake_case(input_string: str) -> str:
    """
    Converts camelCase to snake_case

    >>> camel_case_to_snake_case('CamelCase')
    "camel_case"
    >>> camel_case_to_snake_case('ObiWanKenobi')
    "obi_wan_kenobi"
    """
    characters = []

    for curr_idx, char in enumerate(input_string):
        if curr_idx and char.isupper():
            next_idx = curr_idx + 1
            flag = next_idx >= len(input_string) or input_string[next_idx].isupper()
            prev_char = input_string[curr_idx - 1]

            if prev_char.isupper() and flag:
                pass
            else:
                characters.append("_")
        characters.append(char.lower())

    return "".join(characters)
