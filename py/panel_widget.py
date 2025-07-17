import panel as pn
import xarray as xr
from py import generate_graphs as gg
from py import utils
from datetime import datetime
from flask import session, has_request_context
import os
import uuid
from py import forecasted_graphs as fg
from py import skill_score as ss
import io
from py import attribute as atrb
from py import multi_select_forecasted_graphs as msfg
import traceback

pn.extension()

def get_panel_layout():

    # Custom CSS to enlarge the input fields (year labels)
    custom_css = pn.pane.HTML("""
    <style>
    .bigger-slider input[type='number'] {
        font-size: 18px !important;
        height: 32px;
        padding: 2px 6px;
    }
    .bigger-slider .bk-slider-title {
        font-size: 18px;
        font-weight: bold;
    }
    </style>
    """)


    year_slider = pn.widgets.EditableRangeSlider(
        name='Year Range',
        start=1981, end=datetime.now().year,
        step=1,
        width=600,  # increase the width
        margin=(10, 0),  # optional: adds some vertical spacing
        css_classes=["bigger-slider"]
    )

    update_button = pn.widgets.Button(name='Generate Images', button_type='primary')


    status = pn.pane.Markdown()
    # Create 4 image panes
    image_pane_hurricane = pn.pane.PNG(height=300, width=500)
    image_pane_tc = pn.pane.PNG(height=300, width=500)
    image_pane_ace = pn.pane.PNG(height=300, width=500)
    image_pane_pdi = pn.pane.PNG(height=300, width=500)

    # Arrange them in a grid with captions below each image
    #image_grid = pn.GridSpec(sizing_mode='stretch_both', max_width=1000)
    #image_grid[0, 0] = pn.Column(image_pane_hurricane, pn.pane.Markdown("**Figure 1: Hurricane Frequency**"), margin=(10, 10, 30, 10))
    #image_grid[0, 1] = pn.Column(image_pane_tc, pn.pane.Markdown("**Figure 2: Tropical Cyclone Count**"), margin=(10, 10, 30, 10))
    #image_grid[1, 0] = pn.Column(image_pane_ace, pn.pane.Markdown("**Figure 3: ACE (Accumulated Cyclone Energy)**"), margin=(10, 10, 30, 10))
    #image_grid[1, 1] = pn.Column(image_pane_pdi, pn.pane.Markdown("**Figure 4: Power Dissipation Index (PDI)**"), margin=(10, 10, 30, 10))


    image_grid = pn.GridBox(
        pn.Column(image_pane_hurricane),
        pn.Column(image_pane_tc),
        pn.Column(image_pane_ace),
        pn.Column(image_pane_pdi),
        ncols=2,
        sizing_mode='stretch_width',
        width=1000,
        align='center',
        margin=10,
    )


    # centered_layout = pn.Column(
    # image_grid,
    #align='center',  # horizontally center the contents
    #width=950         # adjust based on your image widths + spacing
    #)



    def get_user_id():
        if has_request_context() and session.get('user_id'):
            return session['user_id']
        else:
            return str(uuid.uuid4())
        
    # This pane contains JavaScript to send a postMessage to the parent page
    message_pane = pn.pane.HTML("""
    <script>
      function notifyParentImagesUpdated() {
        window.parent.postMessage("images_updated", "*");
      }
    </script>
    """)

    def update_plot(event):
        start, end = year_slider.value
        user_id = get_user_id()
        
        try:
            image_pane_hurricane.object = gg.generate_image_for_user(start, end, user_id, 'Hurricane')
            image_pane_tc.object = gg.generate_image_for_user(start, end, user_id, 'Tropical Cyclone')
            image_pane_ace.object = gg.generate_image_for_user(start, end, user_id, 'ACE')
            image_pane_pdi.object = gg.generate_image_for_user(start, end, user_id, 'PDI')
            status.object = f"Images updated for {start}–{end}"
        except Exception as e:
            status.object = f"Error updating images: {e}"

        status.object = f"Images updated for {start}–{end}"
        message_pane.object += "<script>notifyParentImagesUpdated()</script>"

    update_button.on_click(update_plot)

    return pn.Column(
        custom_css,
        pn.pane.Markdown("<h2 style='font-size:28px;'>Interactive Year Selector</h2>", sizing_mode="stretch_width"),
        pn.pane.Markdown("<p style='font-size:18px;'>Use the slider below to select a range of years for plotting.</p>", sizing_mode="stretch_width"),
        year_slider,
        update_button,
        status,
        message_pane,
        image_grid,
        #centered_layout
        sizing_mode="stretch_width",
        #max_width=1600,
        align='center'
    )







def get_forecast_layout():

    # Custom CSS to enlarge the input fields (year labels)
    custom_css = pn.pane.HTML("""
    <style>
    .bigger-slider input[type='number'] {
        font-size: 18px !important;
        height: 32px;
        padding: 2px 6px;
    }
    .bigger-slider .bk-slider-title {
        font-size: 18px;
        font-weight: bold;
    }
    </style>
    """)



    # make a drop down menu for quantity of interest (ex. pdi)
    quantities = ['Hurricane', 'Tropical Cyclone', 'ACE', 'PDI']
    quantity_select = pn.widgets.Select(name='Quantity of Interest', options=quantities, value='Hurricane')
    # or use Dropdown:
    # quantity_select = pn.widgets.Dropdown(name='Quantity of Interest', options=quantities, value='Hurricane')
    # select one (for now) for init month
    init_month_multi_select = pn.widgets.Select(
        name='Initialization Month(s)',
        options=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August'],
        value='June',  # default selection
    )
    # select one (for now) for research center (model)
    #model_multi_select = pn.widgets.MultiChoice(
    #    name='Research Center(s)',
    #    options=['BOM', 'CMCC', 'DWD', 'ECCC', 'ECMWF', 'JMA', 'MF', 'NCEP', 'NMME_NASA', 'NMME_NCEP', 'UKMO'],
    #   placeholder='Select model(s)...'
    #)

    model_multi_select = pn.widgets.Select(
        name='Research Center(s)',
        options=['BOM', 'CMCC', 'DWD', 'ECCC', 'ECMWF', 'JMA', 'MF', 'NCEP', 'NMME_NASA', 'NMME_NCEP', 'UKMO'],
        value = 'ECMWF'
    )


    year_slider = pn.widgets.EditableRangeSlider(
        name='Year Range',
        start=1981, end=datetime.now().year,
        step=1,
        width=600,  # increase the width
        margin=(10, 0),  # optional: adds some vertical spacing
        css_classes=["bigger-slider"]
    )

    update_button = pn.widgets.Button(name='Generate Images', button_type='primary')


    status = pn.pane.Markdown()
    # Create 2 image panes -- one is time series, one is skill score
    image_pane_time_series = pn.pane.PNG(height=300, width=500)
    image_pane_skill_score = pn.pane.PNG(height=300, width=500)
    image_pane_attribute = pn.pane.PNG(height=300, width=500)
    image_pane_reliability = pn.pane.PNG(height=300, width=500)
    image_pane_roc = pn.pane.PNG(height=300, width=500)

    # Arrange them in a grid with captions below each image
    #image_grid = pn.GridSpec(sizing_mode='stretch_both', max_width=1000)
    #image_grid[0, 0] = pn.Column(image_pane_hurricane, pn.pane.Markdown("**Figure 1: Hurricane Frequency**"), margin=(10, 10, 30, 10))
    #image_grid[0, 1] = pn.Column(image_pane_tc, pn.pane.Markdown("**Figure 2: Tropical Cyclone Count**"), margin=(10, 10, 30, 10))
    #image_grid[1, 0] = pn.Column(image_pane_ace, pn.pane.Markdown("**Figure 3: ACE (Accumulated Cyclone Energy)**"), margin=(10, 10, 30, 10))
    #image_grid[1, 1] = pn.Column(image_pane_pdi, pn.pane.Markdown("**Figure 4: Power Dissipation Index (PDI)**"), margin=(10, 10, 30, 10))


    # image_grid = pn.GridBox(
     #   pn.Column(image_pane_time_series),
     #   pn.Column(image_pane_skill_score_mdr),
     #   pn.Column(image_pane_skill_score_trop), 
    #    ncols=2,
      #  sizing_mode='stretch_width',
      #  width=1000,
      #  align='center',
      #  margin=10,
    #)
    # Top image: time series
    # Bottom row: skill scores (MDR and Trop)
    image_grid = pn.Column (
        pn.Row(
            pn.Column(image_pane_time_series),
            sizing_mode='stretch_width',
            align='center'
        ),
        pn.Row(
            pn.Column(image_pane_skill_score),
            sizing_mode='stretch_width',
            align='center'
        ),
        pn.Row(
            pn.Column(image_pane_attribute),
            pn.Column(image_pane_reliability),
            pn.Column(image_pane_roc),
            sizing_mode = 'stretch_width',
            align= 'center'
        ),
        sizing_mode='stretch_width',
        width=1000,
        margin=10,
        align='center'
    )



    # centered_layout = pn.Column(
    # image_grid,
    #align='center',  # horizontally center the contents
    #width=950         # adjust based on your image widths + spacing
    #)



    def get_user_id():
        if has_request_context() and session.get('user_id'):
            return session['user_id']
        else:
            return str(uuid.uuid4())
        
    # This pane contains JavaScript to send a postMessage to the parent page
    message_pane = pn.pane.HTML("""
    <script>
      function notifyParentImagesUpdated() {
        window.parent.postMessage("images_updated", "*");
      }
    </script>
    """)

    def update_plot(event):
        start, end = year_slider.value
        user_id = get_user_id()
        selected_quantity = quantity_select.value
        selected_center = model_multi_select.value
        selected_init_month = init_month_multi_select.value
        
        try:
            # img_bytes = fg.panel_predicted_graph(selected_quantity, start, end, selected_init_month, selected_center)
            # image_pane_time_series.object = io.BytesIO(img_bytes)
            image_pane_time_series.object = fg.panel_predicted_graph(selected_quantity, start, end, selected_init_month, selected_center)
            image_pane_skill_score.object = ss.skill_score_generate_graph(selected_center, selected_init_month, start, end)
            image_pane_attribute.object = atrb.generate_attribute_graph(selected_center, selected_init_month, 'attribute')
            image_pane_reliability.object = atrb.generate_attribute_graph(selected_center, selected_init_month, 'reliability')
            image_pane_roc.object = atrb.generate_attribute_graph(selected_center, selected_init_month, 'roc')
            status.object = f"Images updated for {start}–{end}"
        except Exception as e:
            status.object = f"Error updating images: {e}"

        status.object = f"Images updated for {start}–{end}"
        message_pane.object += "<script>notifyParentImagesUpdated()</script>"

    update_button.on_click(update_plot)

    return pn.Column(
        custom_css,
        pn.pane.Markdown("<h2 style='font-size:28px;'>Interactive Year Selector</h2>", sizing_mode="stretch_width"),
        pn.pane.Markdown("<p style='font-size:18px;'>Use the slider below to select a range of years for plotting.</p>", sizing_mode="stretch_width"),
        quantity_select,
        model_multi_select,
        init_month_multi_select,
        year_slider,
        update_button,
        status,
        message_pane,
        image_grid,
        #pn.Column(image_grid, align='center'),
        #centered_layout
        sizing_mode="stretch_width",
        #max_width=1600,
        align='center'
    )








def get_multi_forecast_layout():

    # Custom CSS to enlarge the input fields (year labels)
    custom_css = pn.pane.HTML("""
    <style>
    .bigger-slider input[type='number'] {
        font-size: 18px !important;
        height: 32px;
        padding: 2px 6px;
    }
    .bigger-slider .bk-slider-title {
        font-size: 18px;
        font-weight: bold;
    }
    </style>
    """)



    # make a drop down menu for quantity of interest (ex. pdi)
    quantities = ['Hurricane', 'Tropical Cyclone', 'ACE', 'PDI']
    quantity_select = pn.widgets.Select(name='Quantity of Interest', options=quantities, value='Hurricane')
    # or use Dropdown:
    # quantity_select = pn.widgets.Dropdown(name='Quantity of Interest', options=quantities, value='Hurricane')
    # select one (for now) for init month
    init_month_multi_select = pn.widgets.MultiChoice(
        name='Initialization Month(s)',
        options=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August'],
        placeholder='Select initialization month(s)...'
    )
    # select one (for now) for research center (model)
    model_multi_select = pn.widgets.MultiChoice(
        name='Research Center(s)',
        options=['Total Unweighted Average', 'Total Weighted Average', 'BOM', 'CMCC', 'DWD', 'ECCC', 'ECMWF', 'JMA', 'MF', 'NCEP', 'NMME_NASA', 'NMME_NCEP', 'UKMO'],
        placeholder='Select model(s)...'
    )

    year_slider = pn.widgets.EditableRangeSlider(
        name='Year Range',
        start=1981, end=datetime.now().year,
        step=1,
        width=600,  # increase the width
        margin=(10, 0),  # optional: adds some vertical spacing
        css_classes=["bigger-slider"]
    )

    update_button = pn.widgets.Button(name='Generate Images', button_type='primary')

    loading_spinner = pn.indicators.LoadingSpinner(
        value=True,            # animate
        visible=False,         # only visible while loading
        width=50,
        height=50,
        color="dark"           # black spinner for white background
    )
    pn.Row(update_button, loading_spinner, align='center'),


    status = pn.pane.Markdown()
    # Create 2 image panes -- one is time series, one is skill score
    image_pane_time_series = pn.pane.PNG(height=300, width=500)
    image_pane_skill_score_mdr = pn.pane.PNG(height=300, width=500)
    image_pane_skill_score_trop = pn.pane.PNG(height=300, width=500)
    image_pane_attribute = pn.pane.PNG(height=300, width=500)
    image_pane_reliability = pn.pane.PNG(height=300, width=500)
    image_pane_roc = pn.pane.PNG(height=300, width=500)

    # Arrange them in a grid with captions below each image
    #image_grid = pn.GridSpec(sizing_mode='stretch_both', max_width=1000)
    #image_grid[0, 0] = pn.Column(image_pane_hurricane, pn.pane.Markdown("**Figure 1: Hurricane Frequency**"), margin=(10, 10, 30, 10))
    #image_grid[0, 1] = pn.Column(image_pane_tc, pn.pane.Markdown("**Figure 2: Tropical Cyclone Count**"), margin=(10, 10, 30, 10))
    #image_grid[1, 0] = pn.Column(image_pane_ace, pn.pane.Markdown("**Figure 3: ACE (Accumulated Cyclone Energy)**"), margin=(10, 10, 30, 10))
    #image_grid[1, 1] = pn.Column(image_pane_pdi, pn.pane.Markdown("**Figure 4: Power Dissipation Index (PDI)**"), margin=(10, 10, 30, 10))


    # image_grid = pn.GridBox(
     #   pn.Column(image_pane_time_series),
     #   pn.Column(image_pane_skill_score_mdr),
     #   pn.Column(image_pane_skill_score_trop), 
    #    ncols=2,
      #  sizing_mode='stretch_width',
      #  width=1000,
      #  align='center',
      #  margin=10,
    #)
    # Top image: time series
    # Bottom row: skill scores (MDR and Trop)

    image_pane_list = []  # list of pn.pane.PNG objects

    # This will hold the dynamic layout for the images
    dynamic_image_container = pn.Column(sizing_mode='stretch_width', align='center')

    image_grid = pn.Column(
        dynamic_image_container,
        sizing_mode='stretch_width',
        align='center',
        margin=10
    )



    # centered_layout = pn.Column(
    # image_grid,
    #align='center',  # horizontally center the contents
    #width=950         # adjust based on your image widths + spacing
    #)



    def get_user_id():
        if has_request_context() and session.get('user_id'):
            return session['user_id']
        else:
            return str(uuid.uuid4())
        
    # This pane contains JavaScript to send a postMessage to the parent page
    message_pane = pn.pane.HTML("""
    <script>
      function notifyParentImagesUpdated() {
        window.parent.postMessage("images_updated", "*");
      }
    </script>
    """)

    def update_plot(event):
        start, end = year_slider.value
        user_id = get_user_id()
        selected_quantity = quantity_select.value
        selected_center = model_multi_select.value
        selected_init_month = init_month_multi_select.value

        loading_spinner.visible = True

        try:
            # Clear old images
            dynamic_image_container.objects.clear()
            image_pane_list.clear()

            # Get list of image bytes
            print('trying')
            img_bytes_list, section_img_count, no_data_messages = msfg.panel_predicted_graph(
                selected_quantity, start, end, selected_init_month, selected_center
            )
            print("LENGTH:")
            print(len(img_bytes_list))
            print("NO DATA MESSAGES:")
            print(no_data_messages)
            

            section_titles = []
            section_subtext = []
            sections = []

            print("SECTION IMG COUNT:")
            print(section_img_count[0])
            if (section_img_count[0] > 0) or (len(no_data_messages[0])>0):
                print("panel weighted avg")
                section_titles.append("<h2 style='font-size:22px; font-weight:bold;'>Forecasts Averaged over All Research Centers")
                subtexts = [f"<p style='font-size:14px; color:#444;'>{text}</p>" for text in no_data_messages[0]]
                section_subtext.append(subtexts)
                sections.append(img_bytes_list[:section_img_count[0]])

                selected_center = list(selected_center)
                selected_center.remove("Total Weighted Average")

            #import sys
            #sys.exit()

            n_multicenter = len(selected_init_month)
            n_multimonth = len(selected_center)

            if (section_img_count[1]>0) or (len(no_data_messages[1])>0):
                section_titles.append("<h2 style='font-size:22px; font-weight:bold;'>Forecasts by Initialization Month for Selected Research Centers")
                subtexts = [f"<p style='font-size:14px; color:#444;'>{text}</p>" for text in no_data_messages[1]]
                section_subtext.append(subtexts)
                sections.append(img_bytes_list[section_img_count[0]:section_img_count[1]+section_img_count[0]])
        
            if (section_img_count[2]>0) or (len(no_data_messages[2])>0):
                section_titles.append("<h2 style='font-size:22px; font-weight:bold;'>Forecasts by Research Center for Each Initialization Month (with Percentiles)")
                subtexts = [f"<p style='font-size:14px; color:#444;'>{text}</p>" for text in no_data_messages[2]]
                section_subtext.append(subtexts)
                sections.append(img_bytes_list[section_img_count[1]+section_img_count[0]:section_img_count[1]+section_img_count[0]+section_img_count[2]])

            if (section_img_count[3]>0) or (len(no_data_messages[3])>0):
                section_titles.append("<h2 style='font-size:22px; font-weight:bold;'>Skill Scores by Research Center and Initialization Month")
                subtexts = [f"<p style='font-size:14px; color:#444;'>{text}</p>" for text in no_data_messages[3]]
                section_subtext.append(subtexts)
                sections.append(img_bytes_list[section_img_count[1]+section_img_count[0]+section_img_count[2]:section_img_count[1]+section_img_count[0]+section_img_count[2]+section_img_count[3]])
            
            if (section_img_count[4]>0) or (len(no_data_messages[4])>0):
                print("LAST PART")
                section_titles.append("<h2 style='font-size:22px; font-weight:bold;'>Attribute/Reliability by Research Center and Initialization Month")
                subtexts = [f"<p style='font-size:14px; color:#444;'>{text}</p>" for text in no_data_messages[4]]
                section_subtext.append(subtexts)
                sections.append(img_bytes_list[section_img_count[1]+section_img_count[0]+section_img_count[2]+section_img_count[3]:])

            
            for i, (title, subtext_list, section_imgs) in enumerate(zip(section_titles, section_subtext, sections)):
                dynamic_image_container.append(pn.pane.HTML(
                    "<hr style='border: none; height: 1px; background-color: black; margin: 10px 0;'>",
                    sizing_mode='stretch_width'
                ))
                dynamic_image_container.append(pn.pane.Markdown(title))
                
                # Append each paragraph separately, so each appears after the title
                for paragraph in subtext_list:
                    dynamic_image_container.append(pn.pane.Markdown(paragraph))


                is_last_section = (i == len(section_titles) - 1)
                valid_imgs = [img for img in section_imgs if img is not None]

                if not is_last_section:
                    # All images in one row
                    row = pn.Row(sizing_mode='stretch_width', align='center')
                    for img_bytes in valid_imgs:
                        try:
                            if not isinstance(img_bytes, (bytes, bytearray)):
                                raise TypeError(f"Expected bytes but got {type(img_bytes)}")
                            pane = pn.pane.PNG(io.BytesIO(img_bytes), height=300, width=500)
                            image_pane_list.append(pane)
                            row.append(pane)
                        except Exception as e:
                            error_str = f"{type(e).__name__}: {e}"
                            traceback.print_exc()
                            status.object = f"Error updating images: {error_str}"
                    dynamic_image_container.append(row)
                else:
                    # Last section: split into rows of 3
                    for j in range(0, len(valid_imgs), 3):
                        row_imgs = valid_imgs[j:j + 3]
                        row = pn.Row(sizing_mode='stretch_width', align='center')
                        for img_bytes in row_imgs:
                            try:
                                pane = pn.pane.PNG(io.BytesIO(img_bytes), height=300, width=500)
                                image_pane_list.append(pane)
                                row.append(pane)
                            except Exception as e:
                                error_str = f"{type(e).__name__}: {e}"
                                traceback.print_exc()
                                status.object = f"Error updating images: {error_str}"
                        dynamic_image_container.append(row)
            
            

            # Create PNG panes and add to layout
           # for img_bytes in img_bytes_list:
            #    pane = pn.pane.PNG(io.BytesIO(img_bytes), height=300, width=500)
            #    image_pane_list.append(pane)
            #    dynamic_image_container.append(pane)

            status.object = f"Images updated for {start}–{end}"

        except Exception as e:
            status.object = f"Error updating images: {e}"
        finally:
            loading_spinner.visible = False

        message_pane.object += "<script>notifyParentImagesUpdated()</script>"
    
    update_button.on_click(update_plot)

    return pn.Column(
        custom_css,
        pn.pane.Markdown("<h2 style='font-size:28px;'>Interactive Year Selector</h2>", sizing_mode="stretch_width"),
        pn.pane.Markdown("<p style='font-size:18px;'>Use the slider below to select a range of years for plotting.</p>", sizing_mode="stretch_width"),
        quantity_select,
        model_multi_select,
        init_month_multi_select,
        year_slider,
        update_button,
        loading_spinner,
        status,
        message_pane,
        image_grid,
        #pn.Column(image_grid, align='center'),
        #centered_layout
        sizing_mode="stretch_width",
        #max_width=1600,
        align='center'
    )
