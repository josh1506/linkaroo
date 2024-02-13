import json

from django.views import generic

from app.url_tracker.utils import get_latest_7_days_total_clicks, get_total_active_urls, get_top_5_links


class UrlOverviewTemplateView(generic.TemplateView):
    template_name = 'app/url_tracker/overview/index.html'

    def get_context_data(self, **kwargs):
        user_url = self.request.user.url.all()

        kwargs['top_links'] = get_top_5_links(user_url)
        kwargs['total_active_url'] = json.dumps(get_total_active_urls(user_url))
        kwargs['latest_total_clicks'] = json.dumps(get_latest_7_days_total_clicks(user_url))

        kwargs['total_links_data'] = json.dumps({
            'active_links_count': 0,
            'recent_7_days_created': [
                ['Acrocanthosaurus (top-spined lizard)', 12.2],
                ['Albertosaurus (Alberta lizard)', 9.1],
                ['Allosaurus (other lizard)', 12.2],
                ['Apatosaurus (deceptive lizard)', 22.9],
                ['Archaeopteryx (ancient wing)', 0.9],
                ['Argentinosaurus (Argentina lizard)', 36.6],
                ['Baryonyx (heavy claws)', 9.1],
                ['Brachiosaurus (arm lizard)', 30.5],
                ['Ceratosaurus (horned lizard)', 6.1],
                ['Coelophysis (hollow form)', 2.7],
                ['Compsognathus (elegant jaw)', 0.9],
                ['Deinonychus (terrible claw)', 2.7],
                ['Diplodocus (double beam)', 27.1],
                ['Dromicelomimus (emu mimic)', 3.4],
                ['Gallimimus (fowl mimic)', 5.5],
                ['Mamenchisaurus (Mamenchi lizard)', 21.0],
                ['Megalosaurus (big lizard)', 7.9],
                ['Microvenator (small hunter)', 1.2],
                ['Ornithomimus (bird mimic)', 4.6],
                ['Oviraptor (egg robber)', 1.5],
                ['Plateosaurus (flat lizard)', 7.9],
                ['Sauronithoides (narrow-clawed lizard)', 2.0],
                ['Seismosaurus (tremor lizard)', 45.7],
                ['Spinosaurus (spiny lizard)', 12.2],
                ['Supersaurus (super lizard)', 30.5],
                ['Tyrannosaurus (tyrant lizard)', 15.2],
                ['Ultrasaurus (ultra lizard)', 30.5],
                ['Velociraptor (swift robber)', 1.8]
            ],
        })

        kwargs['total_clicks_data'] = json.dumps({
            'clicks_count': 0,
            'recent_7_days_created': [
                ['2013', 1000, 400, 200],
                ['2014', 1170, 460, 400],
                ['2015', 660, 1120, 300],
                ['2016', 1030, 540, 700]
            ]
        })

        return kwargs
