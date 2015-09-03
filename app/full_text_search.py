#!/usr/bin/python2.7
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import re

from google.appengine.api import search as appengine_search

import model


import script_variant
# The index name for full text search
PERSON_FULL_TEXT_INDEX_NAME = 'person_information'

def search(repo, query_txt, max_results):
    """
    Searches person with index.
    Args:
        repo: The name of repository
        query_txt: Search query
        max_results: The max number of results you want.(Maximum: 1000)

    Returns:
        results[<model.Person>, ...]

    Raises:
        search.Error: An error occurred when the index name is unknown
                      or the query has syntax error.
    """
    #TODO: Sanitaize query_txt
    results = []
    if not query_txt:
        return results
    index = appengine_search.Index(name=PERSON_FULL_TEXT_INDEX_NAME)
    query_txt += ' AND (repo: ' + repo + ')'
    options = appengine_search.QueryOptions(
        limit=max_results,
        returned_fields=['record_id'])
    index_results = index.search(appengine_search.Query(
        query_string=query_txt, options=options))
    for document in index_results:
        id = document.fields[0].value
        result = model.Person.get(repo, id, filter_expired=True)
        if result:
            results.append(result)
    return results


def create_document(record_id, repo, **kwargs):
    """
    Creates document for full text search.
    It should be called in add_record_to_index method.
    """
    doc_id = repo + ':' + record_id
    fields = []
    fields.append(appengine_search.TextField(name='repo', value=repo))
    fields.append(appengine_search.TextField(name='record_id', value=record_id))
    for field in kwargs:
        script_varianted_value = script_variant.script_variant_western(
            kwargs[field])
        fields.append(
            appengine_search.TextField(name=field, value=script_varianted_value))
    return appengine_search.Document(doc_id=doc_id, fields=fields)


def add_record_to_index(person):
    """
    Adds person record to index.
    Raises:
        search.Error: An error occurred when the document could not be indexed
                      or the query has a syntax error.
    """
    index = appengine_search.Index(name=PERSON_FULL_TEXT_INDEX_NAME)
    index.put(create_document(
        person.record_id,
        person.repo,
        given_name=person.given_name,
        family_name=person.family_name,
        full_name=person.full_name,
        alternate_names=person.alternate_names))


def delete_record_from_index(person):
    """
    Deletes person record from index.
    Args:
        person: Person who should be removed
    Raises:
        search.Error: An error occurred when the index name is unknown
                      or the query has a syntax error.
    """
    index = appengine_search.Index(name=PERSON_FULL_TEXT_INDEX_NAME)
    doc_id = person.repo + ':' + person.record_id
    index.delete(doc_id)