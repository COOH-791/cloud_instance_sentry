numtext = "213527.92"


def number_to_rmb(num_text: str):
    """
    将数字转换为人民币书写格式
    """
    num_text = '{:.2f}'.format(eval(num_text))
    num_dx = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
    rmb_unit = ['分', '角', '元', '拾', '佰', '仟', '万', '拾', '佰', '仟', '亿']
    temp_text = '零'
    temp_id = 0

    for i in num_text[::-1]:
        if i != '.':
            if int(i) == 0:
                if rmb_unit[temp_id] in ['元', '万']:
                    temp_text = rmb_unit[temp_id] + temp_text
                elif temp_text[0] not in ['零', '元', '万']:
                    temp_text = '零' + temp_text
            else:
                temp_text = num_dx[int(i)] + rmb_unit[temp_id] + temp_text
            temp_id += 1
    temp_text = temp_text[:-1]

    if '亿万' in temp_text:
        temp_text = temp_text.replace('亿万', '亿')

    return temp_text


number_to_rmb("213527.12")
