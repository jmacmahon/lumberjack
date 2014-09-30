# -*- coding: utf-8 -*-
##
## This file is part of Lumberjack.
## Copyright (C) 2014 CERN.
##
## Lumberjack is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Lumberjack is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Lumberjack; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from __future__ import absolute_import
import unittest
import time

import lumberjack

from .common import LumberjackTestCase, HOSTS

INTERVAL_SHORT = 2
INTERVAL_LONG = 10*INTERVAL_SHORT
MAX_QUEUE_LENGTH = 20

class AsyncTestCase(LumberjackTestCase):
    def setUp(self):
        super(AsyncTestCase, self).setUp()
        self.lj = lumberjack.Lumberjack(hosts=HOSTS,
                                        index_prefix=self.index_prefix,
                                        interval=INTERVAL_SHORT,
                                        max_queue_length=MAX_QUEUE_LENGTH)
        self.lj.register_schema(__name__, {'_source': {'enabled': True}})
        self.elasticsearch = self.lj.elasticsearch

    def testParamsPassedToActionQueue(self):
        self.assertEqual(INTERVAL_SHORT, self.lj.action_queue.interval)
        self.assertEqual(MAX_QUEUE_LENGTH,
                         self.lj.action_queue.max_queue_length)

    #Tests: max_queue_len, flushing, timeouts, running
    def testChangeUpdateInterval(self):
        self.lj.action_queue.queue_index(suffix='test',
                                         doc_type=__name__,
                                         body={'message': 'testA'})
        time.sleep(INTERVAL_SHORT + 3)
        res = self.elasticsearch.search(
            index=self.index_prefix + '*', doc_type=__name__,
            body={
                'query': {
                    'match': {
                        'message': 'testA'
                    }
                }
            })
        self.assertEqual(res['hits']['total'], 1)

        self.lj.action_queue.interval = INTERVAL_LONG
        time.sleep(1)
        self.lj.trigger_flush()

        self.lj.action_queue.queue_index(suffix='test',
                                         doc_type=__name__,
                                         body={'message': 'testB'})
        time.sleep(INTERVAL_SHORT + 3)
        b_query = {
                'query': {
                    'match': {
                        'message': 'testB'
                    }
                }
            }
        res = self.elasticsearch.search(
            index=self.index_prefix + '*', doc_type=__name__,
            body=b_query)
        self.assertEqual(res['hits']['total'], 0)
        
        time.sleep(INTERVAL_LONG)
        res = self.elasticsearch.search(
            index=self.index_prefix + '*', doc_type=__name__,
            body=b_query)
        self.assertEqual(res['hits']['total'], 1)
    
    def _testMaxQueueLen(self):
        pass

def suite():
    suite = unittest.makeSuite(AsyncTestCase, 'test')
    return suite